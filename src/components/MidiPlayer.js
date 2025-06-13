import React, { useState, useRef, useEffect } from 'react';
import './MidiPlayer.css';

const MidiPlayer = ({ sequence, onBellPlay }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const playerRef = useRef(null);

    const stopPlayback = () => {
        if (playerRef.current) {
            playerRef.current.forEach(timeout => clearTimeout(timeout));
            playerRef.current = null;
        }
        setIsPlaying(false);
        setProgress(0);
    };

    const playSequence = () => {
        if (!sequence || sequence.length === 0) return;

        stopPlayback();
        setIsPlaying(true);

        const startTime = Date.now();
        const totalDuration = sequence[sequence.length - 1].time;
        playerRef.current = [];

        sequence.forEach((event, index) => {
            const timeout = setTimeout(() => {
                onBellPlay(event.note);

                const elapsed = Date.now() - startTime;
                const percentage = (elapsed / totalDuration) * 100;
                setProgress(Math.min(percentage, 100));

                if (index === sequence.length - 1) {
                    setTimeout(stopPlayback, 500);
                }
            }, event.time);

            playerRef.current.push(timeout);
        });
    };

    useEffect(() => {
        return () => stopPlayback();
    }, []);

    return (
        <div className="midi-player">
            <div className="controls">
                <button
                    onClick={isPlaying ? stopPlayback : playSequence}
                    className={isPlaying ? 'stop' : 'play'}
                >
                    {isPlaying ? 'Stop' : 'Play'}
                </button>
            </div>
            <div className="progress-container">
                <div className="progress-bar">
                    <div className="progress" style={{ width: `${progress}%` }} />
                </div>
                <div className="progress-label">{Math.round(progress)}%</div>
            </div>
        </div>
    );
};

export default MidiPlayer;