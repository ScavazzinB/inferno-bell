import mido
import numpy as np
import time
import threading
import simpleaudio as sa
from scipy.cluster.hierarchy import linkage, fcluster

class TrackSelector:
    def __init__(self, midi, num_clusters=3):
        self.midi = midi
        self.num_clusters = num_clusters

    def select_best_track(self):
        histograms, valid = [], []
        for i, tr in enumerate(self.midi.tracks):
            hist = np.zeros(128)
            for msg in tr:
                if msg.type == 'note_on' and msg.velocity > 0:
                    hist[msg.note] += 1
            if hist.sum() > 0:
                histograms.append(hist)
                valid.append(i)
        if not histograms:
            return self.midi.tracks[0] if self.midi.tracks else None
        if len(histograms) == 1:
            return self.midi.tracks[valid[0]]
        linked = linkage(histograms, method='ward')
        clusters = fcluster(linked, t=self.num_clusters, criterion='maxclust')
        counts = {}
        for idx, cl in zip(valid, clusters):
            counts.setdefault(cl, 0)
            counts[cl] += sum(1 for msg in self.midi.tracks[idx]
                               if msg.type == 'note_on' and msg.velocity > 0)
        best_cluster = max(counts, key=counts.get)
        for idx, cl in zip(valid, clusters):
            if cl == best_cluster:
                return self.midi.tracks[idx]
        return self.midi.tracks[valid[0]]

class NoteFilter:
    def __init__(self, min_duration_sec=0.05):
        self.min_duration_sec = min_duration_sec

    def filter_track(self, track):
        abs_t = 0
        ons = {}
        evts = []
        for msg in track:
            abs_t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                ons[msg.note] = abs_t
            elif msg.type in ('note_off',) or (msg.type == 'note_on' and msg.velocity == 0):
                start = ons.pop(msg.note, None)
                if start is not None:
                    duration = abs_t - start
                    evts.append({'note': msg.note, 'time': start, 'duration': duration})

        # Sort events by time
        evts.sort(key=lambda e: e['time'])

        # Modified filtering to keep more notes
        filtered = []
        i = 0
        while i < len(evts):
            t0 = evts[i]['time']
            group = [evts[i]]
            i += 1
            while i < len(evts) and evts[i]['time'] == t0:
                group.append(evts[i])
                i += 1

            # Take the highest 2 notes in dense sections instead of dropping them
            if len(group) >= 3:
                group.sort(key=lambda e: e['note'], reverse=True)
                group = group[:2]  # Keep top 2 notes

            filtered.extend(group)

        return filtered

class MelodyDetector:
    def __init__(self, bell_map=None, bell_samples=None):
        self.bell_map = bell_map or {0: 'Do', 2: 'Ré', 4: 'Mi', 5: 'Fa', 7: 'Sol'}
        self.allowed = sorted(self.bell_map.keys())
        self.filterer = NoteFilter()
        self.samples = {}
        if bell_samples:
            for name, path in bell_samples.items():
                try:
                    self.samples[name] = sa.WaveObject.from_wave_file(path)
                except Exception as e:
                    print(f"Error loading sample {name}: {e}")

    def _map_note(self, pc):
        lo, hi = self.allowed[0], self.allowed[-1]
        if pc <= lo:
            return lo
        if pc >= hi:
            return hi
        return min(self.allowed, key=lambda p: min((pc - p) % 12, (p - pc) % 12))

    def skyline(self, events):
        from itertools import groupby
        seq = []
        for t, group in groupby(sorted(events, key=lambda e: e['time']), key=lambda e: e['time']):
            top = max(group, key=lambda e: e['note'])
            seq.append(top)
        return seq

    def extract(self, midi):
        tpq = midi.ticks_per_beat
        tempo = 500000
        for tr in midi.tracks:
            for msg in tr:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    break
        track = TrackSelector(midi).select_best_track()
        if not track:
            return []
        track.midi = midi
        evts = self.filterer.filter_track(track)
        if not evts:
            return []
        skyline_evts = self.skyline(evts)
        seq_out = []

        # Convert to absolute times in milliseconds
        for n in skyline_evts:
            t_seconds = mido.tick2second(n['time'], tpq, tempo)
            d = mido.tick2second(n['duration'], tpq, tempo)
            pc = n['note'] % 12
            m = self._map_note(pc)
            seq_out.append({
                'note': self.bell_map[m],
                'time': int(t_seconds * 1000),  # Convert to milliseconds
                'duration': d
            })

        # Convert absolute times to relative delays
        seq_out = sorted(seq_out, key=lambda e: e['time'])
        if seq_out:
            prev_time = 0
            for i in range(len(seq_out)):
                curr_time = seq_out[i]['time']
                seq_out[i]['time'] = curr_time - prev_time
                prev_time = curr_time

        return seq_out

    def play_sequence(self, seq):
        """
        Joue la séquence en respectant le timing relatif entre les notes.
        """
        if not self.samples:
            raise RuntimeError("No samples loaded.")

        seq = sorted(seq, key=lambda e: e['time'])
        start_time = time.time()
        play_objs = []  # Keep track of all playing objects

        for ev in seq:
            # Calculate wait time until this note should play
            wait = ev['time'] - (time.time() - start_time)
            if wait > 0:
                time.sleep(wait)

            # Play the note without waiting for it to finish
            wave_obj = self.samples.get(ev['note'])
            if wave_obj:
                play_obj = wave_obj.play()
                play_objs.append(play_obj)

        # Optionally wait for all sounds to finish
        for play_obj in play_objs:
            play_obj.wait_done()