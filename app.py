from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL") or "sqlite:///salary_planner.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default="MAD")
    language = db.Column(db.String(5), default="fr")


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float, default=0)
    icon = db.Column(db.String(20), default="💰")
    is_savings = db.Column(db.Boolean, default=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.relationship("Category")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def category_spent(category_id):
    value = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        Transaction.category_id == category_id
    ).scalar()
    return float(value or 0)



def reset_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="password-reset")


def make_reset_token(user):
    return reset_serializer().dumps({"user_id": user.id, "email": user.email})


def verify_reset_token(token, max_age=1800):
    try:
        data = reset_serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    user = db.session.get(User, int(data.get("user_id", 0)))
    if not user or user.email != data.get("email"):
        return None
    return user


@app.route("/")
def index():
    if current_user.is_authenticated:
        if Category.query.filter_by(user_id=current_user.id).count() == 0:
            return redirect(url_for("onboarding"))
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.")
            return redirect(url_for("register"))

        user = User(
            name=request.form["name"].strip(),
            email=email,
            password_hash=generate_password_hash(request.form["password"]),
            language=request.form.get("language", "fr"),
            currency=request.form.get("currency", "MAD"),
            salary=0
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("onboarding"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            if Category.query.filter_by(user_id=user.id).count() == 0:
                return redirect(url_for("onboarding"))
            return redirect(url_for("dashboard"))
        flash("Email ou mot de passe incorrect.")
    return render_template("login.html")



@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    reset_link = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # Message volontairement identique, que l'adresse existe ou non.
        flash("Si un compte correspond à cette adresse, une procédure de réinitialisation a été préparée.")

        if user:
            token = make_reset_token(user)
            reset_link = url_for("reset_password", token=token, _external=True)

        # En développement local, on affiche le lien pour pouvoir tester.
        # En production, ce lien devra être envoyé par email et ne pas être affiché.
        return render_template("forgot_password.html", reset_link=reset_link)

    return render_template("forgot_password.html", reset_link=None)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash("Ce lien de réinitialisation est invalide ou a expiré.")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.")
            return render_template("reset_password.html")

        if password != confirm:
            flash("Les deux mots de passe ne correspondent pas.")
            return render_template("reset_password.html")

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        flash("Mot de passe modifié avec succès. Tu peux maintenant te connecter.")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/logout")
@login_required
def logout():
    session.pop("budget_draft", None)
    logout_user()
    return redirect(url_for("index"))


@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if request.method == "POST":
        salary = float(request.form.get("salary") or 0)
        currency = request.form.get("currency", "MAD")

        names = request.form.getlist("responsibility_name[]")
        amounts = request.form.getlist("responsibility_amount[]")
        icons = request.form.getlist("responsibility_icon[]")

        responsibilities = []
        for index, name in enumerate(names):
            name = name.strip()
            if not name:
                continue
            try:
                amount = float(amounts[index] or 0)
            except (ValueError, IndexError):
                amount = 0
            icon = icons[index].strip() if index < len(icons) and icons[index].strip() else "💳"
            if amount > 0:
                responsibilities.append({
                    "name": name,
                    "amount": round(amount, 2),
                    "icon": icon
                })

        if salary <= 0:
            flash("Indique un salaire supérieur à 0.")
            return redirect(url_for("onboarding"))

        if not responsibilities:
            flash("Ajoute au moins une responsabilité.")
            return redirect(url_for("onboarding"))

        total_responsibilities = round(sum(x["amount"] for x in responsibilities), 2)
        remaining = round(salary - total_responsibilities, 2)

        if remaining < 0:
            flash("Le total de tes responsabilités dépasse ton salaire. Ajuste les montants.")
            return render_template(
                "onboarding.html",
                salary=salary,
                currency=currency,
                responsibilities=responsibilities
            )

        session["budget_draft"] = {
            "salary": salary,
            "currency": currency,
            "responsibilities": responsibilities
        }
        return redirect(url_for("analysis"))

    return render_template(
        "onboarding.html",
        salary=current_user.salary if current_user.salary else "",
        currency=current_user.currency,
        responsibilities=[]
    )


@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis():
    draft = session.get("budget_draft")
    if not draft:
        return redirect(url_for("onboarding"))

    salary = float(draft["salary"])
    responsibilities = draft["responsibilities"]
    fixed_total = round(sum(float(r["amount"]) for r in responsibilities), 2)
    remaining = round(max(salary - fixed_total, 0), 2)
    ratio = round((fixed_total / salary) * 100, 1) if salary else 0

    if remaining > 0:
        suggested_savings = round(remaining * 0.50, 2)
        suggested_emergency = round(remaining * 0.20, 2)
        suggested_flexible = round(remaining - suggested_savings - suggested_emergency, 2)
    else:
        suggested_savings = suggested_emergency = suggested_flexible = 0

    if request.method == "POST":
        savings = max(float(request.form.get("savings") or 0), 0)
        emergency = max(float(request.form.get("emergency") or 0), 0)
        flexible = max(float(request.form.get("flexible") or 0), 0)

        suggested_total = round(savings + emergency + flexible, 2)
        if suggested_total > remaining + 0.01:
            flash("La répartition proposée dépasse le montant restant.")
            return redirect(url_for("analysis"))

        # Remplacer l'ancien budget seulement au moment de la confirmation.
        Transaction.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
        Category.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)

        current_user.salary = salary
        current_user.currency = draft["currency"]

        for r in responsibilities:
            db.session.add(Category(
                user_id=current_user.id,
                name=r["name"],
                budget=float(r["amount"]),
                icon=r["icon"],
                is_savings=False
            ))

        if savings > 0:
            db.session.add(Category(
                user_id=current_user.id,
                name="Épargne",
                budget=savings,
                icon="🐷",
                is_savings=True
            ))
        if emergency > 0:
            db.session.add(Category(
                user_id=current_user.id,
                name="Urgences",
                budget=emergency,
                icon="🛟",
                is_savings=False
            ))
        if flexible > 0:
            db.session.add(Category(
                user_id=current_user.id,
                name="Personnel & plaisir",
                budget=flexible,
                icon="🌸",
                is_savings=False
            ))

        db.session.commit()
        session.pop("budget_draft", None)
        return redirect(url_for("dashboard"))

    return render_template(
        "analysis.html",
        draft=draft,
        fixed_total=fixed_total,
        remaining=remaining,
        ratio=ratio,
        suggested_savings=suggested_savings,
        suggested_emergency=suggested_emergency,
        suggested_flexible=suggested_flexible
    )


@app.route("/dashboard")
@login_required
def dashboard():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    if not categories:
        return redirect(url_for("onboarding"))

    cards = []
    total_used = 0.0
    total_planned = 0.0
    total_savings_planned = 0.0
    total_savings_used = 0.0
    total_savings_remaining = 0.0

    for category in categories:
        spent = category_spent(category.id)
        remaining = round(max(category.budget - spent, 0), 2)
        pct = 0 if category.budget <= 0 else min(round((spent / category.budget) * 100), 100)

        cards.append({
            "category": category,
            "spent": spent,
            "remaining": remaining,
            "pct": pct
        })

        total_planned += category.budget
        total_used += spent

        if category.is_savings:
            total_savings_planned += category.budget
            total_savings_used += spent
            total_savings_remaining += remaining

    total_remaining_categories = round(sum(c["remaining"] for c in cards), 2)
    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.created_at.desc()
    ).limit(8).all()

    return render_template(
        "dashboard.html",
        cards=cards,
        txs=txs,
        total_used=round(total_used, 2),
        total_planned=round(total_planned, 2),
        total_savings_planned=round(total_savings_planned, 2),
        total_savings_used=round(total_savings_used, 2),
        total_savings_remaining=round(total_savings_remaining, 2),
        total_remaining_categories=total_remaining_categories
    )


@app.route("/spend")
@login_required
def spend_grid():
    categories = Category.query.filter_by(
        user_id=current_user.id
    ).all()

    cards = []
    for category in categories:
        spent = category_spent(category.id)
        cards.append({
            "category": category,
            "spent": spent,
            "remaining": round(max(category.budget - spent, 0), 2)
        })

    return render_template("spend_grid.html", cards=cards)


@app.route("/spend/<int:category_id>", methods=["GET", "POST"])
@login_required
def spend_category(category_id):
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first_or_404()

    spent = category_spent(category.id)
    remaining = round(max(category.budget - spent, 0), 2)

    if request.method == "POST":
        amount = float(request.form.get("amount") or 0)
        description = request.form.get("description", "").strip()

        if amount <= 0:
            flash("Le montant doit être supérieur à 0.")
            return redirect(url_for("spend_category", category_id=category.id))

        if amount > remaining:
            flash(f"Il ne reste que {remaining:.2f} {current_user.currency} dans cette catégorie.")
            return redirect(url_for("spend_category", category_id=category.id))

        db.session.add(Transaction(
            user_id=current_user.id,
            category_id=category.id,
            amount=amount,
            description=description
        ))
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template(
        "spend_category.html",
        category=category,
        spent=spent,
        remaining=remaining
    )


@app.route("/reconfigure")
@login_required
def reconfigure():
    session.pop("budget_draft", None)
    return redirect(url_for("onboarding"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
