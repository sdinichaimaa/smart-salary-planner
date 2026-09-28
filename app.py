from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL") or "sqlite:///salary_planner.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

TRANSLATIONS = {
    "fr": {
        "app_name":"Smart Salary Planner","hello":"Bonjour","dashboard":"Mon budget",
        "salary":"Salaire","spent":"Dépensé","remaining":"Disponible","savings":"Épargne",
        "add_expense":"Ajouter une dépense","categories":"Catégories","settings":"Paramètres",
        "logout":"Déconnexion","login":"Connexion","register":"Créer un compte","email":"Email",
        "password":"Mot de passe","name":"Prénom / Nom","save":"Enregistrer",
        "amount":"Montant","description":"Description","category":"Catégorie",
        "monthly_salary":"Salaire mensuel","language":"Langue","currency":"Devise",
        "recent":"Dernières dépenses","welcome":"Ton argent, mais plus simple ✨",
        "welcome_sub":"Planifie ton salaire, suis tes dépenses et avance vers tes objectifs sans stress.",
        "start":"Commencer","discover":"Découvrir","setup_title":"Configurons ton budget 💖",
        "setup_sub":"Indique ton salaire et nous préparons une première répartition.",
        "no_tx":"Aucune dépense enregistrée pour le moment.",
        "budget":"Budget","add_category":"Ajouter une catégorie"
    },
    "en": {
        "app_name":"Smart Salary Planner","hello":"Hello","dashboard":"My budget",
        "salary":"Salary","spent":"Spent","remaining":"Available","savings":"Savings",
        "add_expense":"Add expense","categories":"Categories","settings":"Settings",
        "logout":"Logout","login":"Login","register":"Create account","email":"Email",
        "password":"Password","name":"Name","save":"Save","amount":"Amount",
        "description":"Description","category":"Category","monthly_salary":"Monthly salary",
        "language":"Language","currency":"Currency","recent":"Recent expenses",
        "welcome":"Your money, made simpler ✨",
        "welcome_sub":"Plan your salary, track spending and move toward your goals with less stress.",
        "start":"Get started","discover":"Discover","setup_title":"Let's set up your budget 💖",
        "setup_sub":"Enter your salary and we’ll create a first budget structure.",
        "no_tx":"No expenses yet.","budget":"Budget","add_category":"Add category"
    },
    "ar": {
        "app_name":"منظم الراتب الذكي","hello":"مرحبا","dashboard":"ميزانيتي",
        "salary":"الراتب","spent":"المصروف","remaining":"المتاح","savings":"الادخار",
        "add_expense":"إضافة مصروف","categories":"الفئات","settings":"الإعدادات",
        "logout":"تسجيل الخروج","login":"تسجيل الدخول","register":"إنشاء حساب",
        "email":"البريد الإلكتروني","password":"كلمة المرور","name":"الاسم","save":"حفظ",
        "amount":"المبلغ","description":"الوصف","category":"الفئة",
        "monthly_salary":"الراتب الشهري","language":"اللغة","currency":"العملة",
        "recent":"آخر المصاريف","welcome":"أموالك بطريقة أبسط ✨",
        "welcome_sub":"خطط لراتبك، تابع مصاريفك وحقق أهدافك المالية بسهولة.",
        "start":"ابدأ الآن","discover":"اكتشف","setup_title":"لنجهز ميزانيتك 💖",
        "setup_sub":"أدخل راتبك وسنجهز لك أول تقسيم للميزانية.",
        "no_tx":"لا توجد مصاريف مسجلة بعد.","budget":"الميزانية","add_category":"إضافة فئة"
    }
}

def current_lang():
    if current_user.is_authenticated:
        return current_user.language or "fr"
    return session.get("lang", "fr")

def t(key):
    lang = current_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)

app.jinja_env.globals["t"] = t
app.jinja_env.globals["current_lang"] = current_lang

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

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/lang/<lang>")
def set_lang(lang):
    if lang not in ("fr","en","ar"):
        lang = "fr"
    session["lang"] = lang
    if current_user.is_authenticated:
        current_user.language = lang
        db.session.commit()
    return redirect(request.referrer or url_for("index"))

@app.route("/register", methods=["GET","POST"])
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
            language=request.form.get("language","fr"),
            currency=request.form.get("currency","MAD")
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("setup"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Email ou mot de passe incorrect.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/setup", methods=["GET","POST"])
@login_required
def setup():
    if request.method == "POST":
        current_user.salary = float(request.form.get("salary") or 0)
        current_user.currency = request.form.get("currency","MAD")
        current_user.language = request.form.get("language","fr")
        db.session.commit()

        if Category.query.filter_by(user_id=current_user.id).count() == 0:
            defaults = [
                ("Famille", 500, "❤️", False),
                ("Transport", 800, "🚗", False),
                ("Shopping & sorties", 1000, "🛍️", False),
                ("Épargne", 1500, "🐷", True),
                ("Urgences", 400, "🚨", False),
                ("Divers", 200, "✨", False),
            ]
            for name, budget, icon, is_savings in defaults:
                db.session.add(Category(
                    user_id=current_user.id, name=name, budget=budget,
                    icon=icon, is_savings=is_savings
                ))
            db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("setup.html")

@app.route("/dashboard")
@login_required
def dashboard():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    txs = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()

    data = []
    total_spent = 0.0
    total_savings = 0.0

    for c in categories:
        spent = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category_id == c.id
        ).scalar()

        spent = float(spent or 0)
        remaining = max(c.budget - spent, 0)
        pct = 0 if c.budget <= 0 else min(round(spent / c.budget * 100), 100)

        data.append({
            "category": c,
            "spent": spent,
            "remaining": remaining,
            "pct": pct
        })

        if c.is_savings:
            total_savings += c.budget
        else:
            total_spent += spent

    available = max(current_user.salary - total_spent - total_savings, 0)

    return render_template(
        "dashboard.html",
        data=data,
        txs=txs,
        total_spent=total_spent,
        total_savings=total_savings,
        available=available
    )

@app.route("/expense", methods=["GET","POST"])
@login_required
def expense():
    categories = Category.query.filter_by(user_id=current_user.id, is_savings=False).all()

    if request.method == "POST":
        category_id = int(request.form["category_id"])
        category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
        amount = float(request.form["amount"])

        db.session.add(Transaction(
            user_id=current_user.id,
            category_id=category.id,
            amount=amount,
            description=request.form.get("description","").strip()
        ))
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("expense.html", categories=categories)

@app.route("/categories", methods=["GET","POST"])
@login_required
def categories():
    if request.method == "POST":
        db.session.add(Category(
            user_id=current_user.id,
            name=request.form["name"].strip(),
            budget=float(request.form.get("budget") or 0),
            icon=request.form.get("icon") or "💰",
            is_savings=bool(request.form.get("is_savings"))
        ))
        db.session.commit()
        return redirect(url_for("categories"))

    items = Category.query.filter_by(user_id=current_user.id).all()
    return render_template("categories.html", categories=items)

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    if request.method == "POST":
        current_user.salary = float(request.form.get("salary") or 0)
        current_user.currency = request.form.get("currency","MAD")
        current_user.language = request.form.get("language","fr")
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("settings.html")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
