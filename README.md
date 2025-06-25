# Inferno Bells

Inferno Bells est une application web interactive qui transforme des fichiers MIDI en séquences de cloches simplifiées, permettant aux utilisateurs de visualiser et d'entendre des mélodies à travers une interface ludique.

## 🎺 Fonctionnalités Clés

### 🔔 Interface des Cloches

* Affichage visuel de 5 cloches distinctes : Do, Ré, Mi, Fa, Sol
* Les utilisateurs peuvent cliquer sur les cloches pour jouer les notes correspondantes
* Mode édition disponible pour positionner et redimensionner les cloches

### 🎵 Traitement MIDI

* Import de fichiers MIDI depuis l'interface frontend
* Le backend Python extrait la mélodie principale
* Conversion des données MIDI complexes en séquences adaptées aux cloches

### ▶️ Système de Lecture

* Lecture des mélodies extraites via l'interface des cloches
* Retour visuel : les cloches vibre lorsqu'elles sont jouées
* Suivi de la progression pendant la lecture

## ⚖️ Architecture

### Frontend

* Développé avec React
* Composants : Affichage des Cloches, Import MIDI, Contrôles de Lecture

### Backend

* Serveur Python utilisant Flask
* Traite les fichiers MIDI et détecte la mélodie principale
* Transmet les données de mélodie simplifiées au frontend

### Audio

* Utilise des échantillons sonores de cloches
* La lecture audio est principalement gérée côté navigateur pour une expérience fluide

---

Bonne exploration musicale ! 🎶🔔
