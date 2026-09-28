# Smart Salary Planner — V2

Application Flask responsive pour gérer salaire, responsabilités, dépenses et épargne.

## Inclus
- Landing page cute et responsive
- Inscription / connexion
- Choix FR / EN / AR
- Configuration du salaire
- Catégories de budget
- Ajout de dépenses
- Dashboard avec montants dépensés / restants
- Historique récent
- Compatible TiDB/MySQL via DATABASE_URL
- SQLite automatique en local si DATABASE_URL est vide

## Lancer
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
python app.py
```

Puis ouvrir:
http://127.0.0.1:5000
