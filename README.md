# Smart Salary Planner — V3

## Nouveau parcours
1. Création du compte
2. Saisie du salaire
3. Saisie des responsabilités / charges réelles
4. Analyse automatique
5. Proposition de répartition du reste
6. Création du budget
7. Tableau de bord
8. Grille de catégories pour enregistrer une dépense rapidement

## Important si vous venez de V2
Pour tester le nouveau parcours avec votre ancienne base locale, fermez l'application puis supprimez:
`instance/salary_planner.db`

Au prochain lancement, une base locale vide sera recréée.

## Démarrage
```powershell
cd C:\smart-salary-planner
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
python app.py
```

Ouvrir:
http://127.0.0.1:5000

## TiDB
Laissez DATABASE_URL vide pour SQLite local.
Plus tard, placez l'URL TiDB dans `.env`.


## V3.1 — Réinitialisation du mot de passe
- Lien **Mot de passe oublié ?** sur la page de connexion.
- Jeton sécurisé temporaire avec expiration de 30 minutes.
- En développement local, le lien de réinitialisation s'affiche directement.
- Pour la production, il faudra envoyer ce lien par email (le code est déjà préparé pour cette évolution).


## V3.2 — Utiliser l'épargne
L'épargne est maintenant une catégorie utilisable comme les autres.
Exemple: épargne 1 500 MAD, achat matelas 1 500 MAD => utilisé 1 500, reste épargne 0.
Le dashboard affiche l'épargne prévue, utilisée et restante.
