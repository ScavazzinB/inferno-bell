# server.py
import os
import io
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import mido
from melody_detector import MelodyDetector

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Chemin absolu vers le répertoire du script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Chemins vers les samples de cloches dans le dossier 'public/ressource'
# En partant de backend/, on remonte d'un niveau puis on descend dans public/ressource
bell_dir = os.path.normpath(os.path.join(script_dir, '..', 'public', 'ressource'))
bell_samples = {
    'Do': os.path.join(bell_dir, 'do.wav'),
    'Ré': os.path.join(bell_dir, 'ré.wav'),  # nom de fichier avec accent
    'Mi': os.path.join(bell_dir, 'mi.wav'),
    'Fa': os.path.join(bell_dir, 'fa.wav'),
    'Sol': os.path.join(bell_dir, 'sol.wav')
}

# Vérifier l'existence des fichiers de cloche et loguer
for name, path in bell_samples.items():
    if not os.path.isfile(path):
        logger.error(f"Échantillon introuvable pour {name}: {path}")

# Initialiser l'application Flask
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialiser le détecteur de mélodie avec les samples trouvés
melody_detector = MelodyDetector(bell_samples=bell_samples)

@app.route('/upload_midi', methods=['POST'])
def upload_midi():
    """
    Gère l'upload du fichier MIDI et extrait la mélodie.
    """
    if 'midi_file' not in request.files:
        return jsonify({'error': 'Aucun fichier MIDI fourni'}), 400

    midi_file = request.files['midi_file']
    logger.info(f"Fichier reçu : {midi_file.filename}")

    try:
        midi_data = midi_file.read()
        midi = mido.MidiFile(file=io.BytesIO(midi_data))

        # Extraction de la séquence monophonique
        sequence = melody_detector.extract(midi)

        if sequence:
            logger.info(f"Séquence extraite, {len(sequence)} notes")
            return jsonify({'sequence': sequence}), 200
        else:
            logger.info("Aucune séquence détectée.")
            return jsonify({'error': 'Aucune mélodie détectée', 'sequence': []}), 200

    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier MIDI : {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)