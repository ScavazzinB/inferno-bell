import React, { useState } from 'react';
import './App.css';
import BellsContainer from './components/BellsContainer';
import MidiUploader from './components/MidiUploader';
import MidiPlayer from './components/MidiPlayer';

function App() {
    const [sequence, setSequence] = useState(null);
    const [activeNote, setActiveNote] = useState(null);

    const handleMidiProcessed = (bellSequence) => {
        setSequence(bellSequence);
    };

    const handleBellPlay = (note) => {
        setActiveNote(note);
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>Inferno Bells</h1>
            </header>
            <main>
                <MidiUploader onMidiProcessed={handleMidiProcessed} />
                <BellsContainer activeNote={activeNote} />
                {sequence && <MidiPlayer sequence={sequence} onBellPlay={handleBellPlay} />}
            </main>
            <footer>
                <p>Drop a MIDI file to play it with bells</p>
            </footer>
        </div>
    );
}

export default App;