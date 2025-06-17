# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import io
import mido

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialiser l'application Flask
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/upload_midi', methods=['POST'])
def upload_midi():
    """
    Gère l'upload du fichier MIDI et retourne des informations basiques.
    """
    if 'midi_file' not in request.files:
        return jsonify({'error': 'Aucun fichier MIDI fourni'}), 400

    midi_file = request.files['midi_file']
    logger.info(f"Fichier reçu : {midi_file.filename}")

    try:
        midi_data = midi_file.read()
        midi = mido.MidiFile(file=io.BytesIO(midi_data))

        # Informations basiques sur le fichier MIDI
        tracks_info = []
        for i, track in enumerate(midi.tracks):
            track_name = getattr(track, 'name', f'Track {i}')
            notes_count = sum(1 for msg in track if msg.type == 'note_on' and msg.velocity > 0)
            tracks_info.append({
                'track_id': i,
                'name': track_name,
                'notes_count': notes_count
            })

        # Pour les tests, retourner un tableau vide comme séquence
        dummy_sequence = []

        return jsonify({
            'message': 'Fichier MIDI reçu avec succès',
            'filename': midi_file.filename,
            'tracks': tracks_info,
            'sequence': dummy_sequence
        })

    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier MIDI : {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)