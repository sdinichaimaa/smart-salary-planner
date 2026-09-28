from getpass import getpass
from werkzeug.security import generate_password_hash
from app import app, db, User

with app.app_context():
    print("\n=== Smart Salary Planner - Local Password Reset ===")
    print("Database:", app.config["SQLALCHEMY_DATABASE_URI"])

    users = User.query.order_by(User.id).all()

    if not users:
        print("\nAucun utilisateur trouvé dans cette base.")
        print("Cela signifie probablement que l'application lancée n'utilise pas la base attendue.")
        raise SystemExit(1)

    print("\nComptes trouvés :")
    for u in users:
        print(f"  ID {u.id} | {u.email} | {u.name}")

    email = input("\nEmail du compte à réinitialiser : ").strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user:
        print("\n❌ Aucun compte avec cet email dans CETTE base.")
        print("Vérifie que tu lances bien l'application depuis C:\\smart-salary-planner.")
        raise SystemExit(1)

    password = getpass("Nouveau mot de passe : ")
    confirm = getpass("Confirmer le mot de passe : ")

    if len(password) < 6:
        print("\n❌ Le mot de passe doit contenir au moins 6 caractères.")
        raise SystemExit(1)

    if password != confirm:
        print("\n❌ Les deux mots de passe ne correspondent pas.")
        raise SystemExit(1)

    user.password_hash = generate_password_hash(password)
    db.session.commit()

    print("\n✅ Mot de passe réinitialisé avec succès.")
    print("Compte :", user.email)
    print("Tu peux maintenant relancer l'application et te connecter.")
