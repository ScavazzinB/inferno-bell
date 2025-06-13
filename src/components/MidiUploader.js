import React, { useState } from 'react';
import './MidiUploader.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const MidiUploader = ({ onMidiProcessed }) => {
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0);

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        if (file.size > 5000000) {
            setError('File is too large. Please choose a smaller MIDI file (max 5MB).');
            return;
        }

        setLoading(true);
        setError('');
        setProgress(10);

        const formData = new FormData();
        formData.append('midi_file', file);

        try {
            const response = await fetch(`${API_URL}/upload_midi`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                },
                mode: 'cors'
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Use sequence directly from server response
            const bellSequence = data.sequence.map(note => ({
                note: note.note,
                time: note.time // Server already sends time in milliseconds
            }));

            setProgress(100);
            onMidiProcessed(bellSequence);

        } catch (err) {
            console.error('Upload error:', err);
            setError(`Upload failed: ${err.message}`);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    return (
        <div className="midi-uploader">
            <div className="upload-section">
                <h3>Upload MIDI File</h3>
                <input
                    type="file"
                    accept=".mid,.midi"
                    onChange={handleFileUpload}
                    className="file-input"
                />
            </div>

            {loading && (
                <div className="progress-container">
                    <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${progress}%` }} />
                    </div>
                    <div className="progress-info">
                        <span className="progress-percentage">{progress}%</span>
                    </div>
                </div>
            )}

            {error && (
                <div className="error-container">
                    <div className="error-message">{error}</div>
                </div>
            )}
        </div>
    );
};

export default MidiUploader;