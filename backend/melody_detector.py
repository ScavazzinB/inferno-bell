#!/usr/bin/env python3
"""
Extracteur de mélodie MIDI optimisé pour lecture avec des cloches.
"""

import mido
import numpy as np
import logging
import time
import simpleaudio as sa
from scipy.cluster.hierarchy import linkage, fcluster
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MelodyDetector:
    """Extracteur de mélodie avec adaptation pour cloches."""

    def __init__(self, bell_samples=None):
        """
        Initialisation du détecteur de mélodie avec les échantillons de cloches.

        Args:
            bell_samples: Dictionnaire des échantillons {nom: chemin_fichier}
        """
        # Mapping des notes MIDI vers les noms de cloches
        self.bell_map = {
            0: 'Do',   # C - Do
            2: 'Ré',   # D - Ré
            4: 'Mi',   # E - Mi
            5: 'Fa',   # F - Fa
            7: 'Sol',  # G - Sol
        }
        self.allowed = sorted(list(self.bell_map.keys()))

        # Chargement des échantillons de cloches
        self.samples = {}
        if bell_samples:
            for name, path in bell_samples.items():
                try:
                    self.samples[name] = sa.WaveObject.from_wave_file(path)
                    logger.info(f"Échantillon chargé: {name}")
                except Exception as e:
                    logger.error(f"Erreur de chargement pour {name}: {e}")

    def extract(self, midi):
        """
        Extrait la mélodie d'un fichier MIDI et la convertit pour lecture avec les cloches.

        Args:
            midi: Fichier MIDI

        Returns:
            Séquence de notes prête pour la lecture sur cloches
        """
        logger.info(f"Analyse du fichier MIDI: {len(midi.tracks)} pistes")

        # 1. Analyse initiale du fichier MIDI
        tempo = self._get_tempo(midi)
        tpq = midi.ticks_per_beat

        # 2. Sélection des meilleures pistes pour la mélodie
        best_tracks = self._select_melody_tracks(midi)
        if not best_tracks:
            logger.warning("Aucune piste mélodique identifiée")
            return []

        # 3. Extraire tous les événements de note des pistes sélectionnées
        all_events = self._extract_note_events(midi, best_tracks)
        if not all_events:
            logger.warning("Aucune note extraite")
            return []

        # 4. Créer une représentation temporelle quantifiée
        grid_resolution_ticks = tpq / 8  # 32ème de note
        grid = self._create_time_grid(all_events, grid_resolution_ticks)

        # 5. Construire une mélodie monophonique optimisée pour les cloches
        melody = self._build_monophonic_melody(grid)

        # 6. Convertir en séquence de cloches avec timing relatif
        sequence = self._create_bell_sequence(melody, tpq, tempo)

        logger.info(f"Mélodie extraite: {len(sequence)} notes")
        return sequence

    def _get_tempo(self, midi):
        """Récupère le tempo du fichier MIDI."""
        tempo = 500000  # Tempo par défaut (120 BPM)

        for track in midi.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    return tempo

        return tempo

    def _select_melody_tracks(self, midi):
        """
        Sélectionne les pistes contenant probablement la mélodie.

        Implémente l'approche Best-k Channel décrite dans le papier ISM2005.
        """
        # Ignorer la piste de percussion (canal 10)
        tracks = []
        track_info = []

        # Collecter les informations sur chaque piste
        for i, track in enumerate(midi.tracks):
            # Analyser la piste
            notes = []
            is_percussion = False

            for msg in track:
                if hasattr(msg, 'channel') and msg.channel == 9:  # Canal 10 (index 9) = percussion
                    is_percussion = True
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes.append(msg.note)

            # Ignorer les pistes vides ou de percussion
            if not notes or is_percussion:
                continue

            # Calculer les caractéristiques de la piste
            avg_pitch = sum(notes) / len(notes)
            pitch_range = max(notes) - min(notes)
            note_density = len(notes) / (max([msg.time for msg in track if hasattr(msg, 'time')]) + 1)

            # Calculer l'histogramme des hauteurs (normalisé)
            histogram = np.zeros(12)
            for note in notes:
                histogram[note % 12] += 1
            if histogram.sum() > 0:
                histogram = histogram / histogram.sum()

            # Caractéristiques mélodiques - plus la valeur est haute, plus c'est mélodique
            melodic_score = (
                avg_pitch / 127 * 0.3 +            # Préférer les notes plus hautes
                min(pitch_range / 36, 1.0) * 0.4 + # Préférer une ambitus modéré
                min(note_density * 10, 1.0) * 0.3  # Préférer une densité moyenne
            )

            tracks.append(i)
            track_info.append({
                'index': i,
                'avg_pitch': avg_pitch,
                'note_count': len(notes),
                'histogram': histogram,
                'melodic_score': melodic_score
            })

        if not track_info:
            return []

        # Si une seule piste, la sélectionner
        if len(track_info) == 1:
            return [track_info[0]['index']]

        # Appliquer le clustering basé sur l'histogramme des hauteurs
        histograms = [info['histogram'] for info in track_info]
        distances = np.zeros((len(histograms), len(histograms)))

        # Calculer les distances entre les histogrammes
        for i in range(len(histograms)):
            for j in range(i+1, len(histograms)):
                dist = np.sum(np.abs(histograms[i] - histograms[j]))
                distances[i, j] = distances[j, i] = dist

        # Nombre de clusters optimal
        num_clusters = min(3, len(track_info))

        # Clustering hiérarchique
        Z = linkage(distances, method='ward')
        clusters = fcluster(Z, t=num_clusters, criterion='maxclust')

        # Sélectionner la meilleure piste de chaque cluster
        selected_tracks = []

        for cluster_id in range(1, num_clusters + 1):
            cluster_members = [info for info, c in zip(track_info, clusters) if c == cluster_id]
            if cluster_members:
                # Sélectionner la piste la plus mélodique du cluster
                best_track = max(cluster_members, key=lambda x: x['melodic_score'])
                selected_tracks.append(best_track['index'])

        logger.info(f"Pistes sélectionnées: {selected_tracks}")
        return selected_tracks

    def _extract_note_events(self, midi, track_indices):
        """
        Extrait tous les événements de note des pistes sélectionnées.

        Returns:
            Liste d'événements {pitch, start, end, velocity}
        """
        events = []

        for track_idx in track_indices:
            track = midi.tracks[track_idx]
            abs_time = 0
            active_notes = {}

            for msg in track:
                abs_time += msg.time

                if msg.type == 'note_on' and msg.velocity > 0:
                    # Début de note
                    active_notes[msg.note] = {
                        'start': abs_time,
                        'velocity': msg.velocity
                    }
                elif (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)) and msg.note in active_notes:
                    # Fin de note
                    start = active_notes[msg.note]['start']
                    velocity = active_notes[msg.note]['velocity']

                    events.append({
                        'pitch': msg.note,
                        'start': start,
                        'end': abs_time,
                        'duration': abs_time - start,
                        'velocity': velocity
                    })

                    del active_notes[msg.note]

        # Trier par temps de début
        return sorted(events, key=lambda e: e['start'])

    def _create_time_grid(self, events, resolution):
        """
        Crée une grille temporelle quantifiée des événements.

        Args:
            events: Liste d'événements de note
            resolution: Résolution de la grille en ticks

        Returns:
            Dictionnaire {position_grille: liste_notes}
        """
        if not events:
            return {}

        # Déterminer la durée totale
        end_time = max(event['end'] for event in events)

        # Créer la grille temporelle
        grid = defaultdict(list)

        for event in events:
            # Quantifier le temps de début
            grid_pos = int(round(event['start'] / resolution)) * resolution

            # Ajouter l'événement à la position quantifiée
            grid[grid_pos].append(event)

        return grid

    def _build_monophonic_melody(self, grid):
        """
        Construit une mélodie monophonique à partir de la grille temporelle.

        Args:
            grid: Grille temporelle {position: liste_notes}

        Returns:
            Liste d'événements monophoniques
        """
        if not grid:
            return []

        melody = []
        last_note_end = 0

        # Parcourir la grille dans l'ordre chronologique
        for pos in sorted(grid.keys()):
            notes = grid[pos]

            # Si aucune note à cette position, continuer
            if not notes:
                continue

            # Si des notes se chevauchent, sélectionner la meilleure
            if pos < last_note_end:
                # Une note est déjà active, décider si on garde la nouvelle
                current_note = melody[-1]

                # Trouver la note la plus haute et la plus forte à cette position
                candidate = max(notes, key=lambda n: n['pitch'] * 0.7 + n['velocity'] * 0.3)

                # Ne remplacer que si la nouvelle note est significativement meilleure
                if candidate['pitch'] > current_note['pitch'] + 3 or candidate['velocity'] > current_note['velocity'] * 1.2:
                    # La nouvelle note est nettement meilleure, remplaçons l'actuelle
                    melody[-1] = candidate
                    last_note_end = candidate['end']
            else:
                # Pas de chevauchement, sélectionner la note la plus saillante
                if len(notes) > 1:
                    # Préférer les notes plus hautes et plus fortes
                    best_note = max(notes, key=lambda n: n['pitch'] * 0.7 + n['velocity'] * 0.3)
                else:
                    best_note = notes[0]

                melody.append(best_note)
                last_note_end = best_note['end']

        return melody

    def _map_to_nearest_bell(self, pitch):
        """Mappe une hauteur MIDI vers la cloche la plus proche."""
        pitch_class = pitch % 12

        if pitch_class <= self.allowed[0]:
            return self.bell_map[self.allowed[0]]
        elif pitch_class >= self.allowed[-1]:
            return self.bell_map[self.allowed[-1]]
        else:
            closest = min(self.allowed, key=lambda p: min((pitch_class - p) % 12, (p - pitch_class) % 12))
            return self.bell_map[closest]

    def _create_bell_sequence(self, melody, tpq, tempo):
        """
        Crée une séquence adaptée aux cloches.

        Args:
            melody: Liste d'événements mélodiques
            tpq: Ticks par noire
            tempo: Tempo en microsecondes par noire

        Returns:
            Séquence avec délais relatifs
        """
        sequence = []

        # Temps minimum entre deux notes consécutives (en ms)
        min_gap_ms = 250

        # Durée minimale d'une note de cloche (en secondes)
        min_duration_sec = 0.3

        if not melody:
            return []

        # Convertir en temps absolu (ms)
        abs_events = []

        for note in melody:
            start_ms = int(mido.tick2second(note['start'], tpq, tempo) * 1000)
            end_ms = int(mido.tick2second(note['end'], tpq, tempo) * 1000)

            # S'assurer que la note est assez longue pour être perceptible
            duration_sec = max(min_duration_sec, (end_ms - start_ms) / 1000)

            abs_events.append({
                'pitch': note['pitch'],
                'bell': self._map_to_nearest_bell(note['pitch']),
                'start_ms': start_ms,
                'duration': duration_sec
            })

        # Convertir en séquence avec délais relatifs
        prev_end_ms = 0

        for i, event in enumerate(abs_events):
            # Calculer le délai depuis la fin de la note précédente
            if i == 0:
                delay_ms = event['start_ms']
            else:
                # Assurer un écart minimum entre les notes
                delay_ms = max(min_gap_ms, event['start_ms'] - prev_end_ms)

            sequence.append({
                'note': event['bell'],
                'time': delay_ms,
                'duration': event['duration']
            })

            # Mettre à jour le temps de fin pour la prochaine note
            prev_end_ms = event['start_ms'] + int(event['duration'] * 1000)

        return sequence

    def play_sequence(self, sequence):
        """
        Joue la séquence de cloches.

        Args:
            sequence: Séquence de notes avec délais relatifs
        """
        if not self.samples:
            logger.error("Aucun échantillon chargé")
            return

        logger.info(f"Lecture de {len(sequence)} notes")

        # Jouer chaque note séquentiellement
        for i, event in enumerate(sequence):
            # Attendre le délai avant cette note
            if event['time'] > 0:
                time.sleep(event['time'] / 1000)

            # Jouer la cloche
            bell_name = event['note']
            sample = self.samples.get(bell_name)

            if sample:
                logger.info(f"Cloche {bell_name} - Note {i+1}/{len(sequence)}")
                play_obj = sample.play()

                # Attendre la durée de la note
                time.sleep(event['duration'])
            else:
                logger.warning(f"Échantillon manquant pour {bell_name}")
                time.sleep(0.3)  # Pause par défaut