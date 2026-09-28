# Correctif mot de passe

Copier `reset_password_local.py` dans:

C:\smart-salary-planner

Puis:

1. Arrêter Flask avec Ctrl+C
2. Vérifier le dossier:
   cd C:\smart-salary-planner
3. Activer l'environnement:
   .\.venv\Scripts\Activate.ps1
4. Exécuter:
   python reset_password_local.py

Le script affiche:
- la base réellement utilisée
- les comptes réellement présents
- puis permet de changer le mot de passe directement dans cette même base

Ensuite:
python app.py
