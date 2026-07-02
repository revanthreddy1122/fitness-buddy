"""
Fitness Buddy – Main Flask Application
"""
import os
from datetime import datetime, date
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, bcrypt, User, FitnessProfile, HabitLog, WeightLog, MealPlan, ChatMessage, Notification
from watsonx_ai import chat_with_granite, generate_meal_plan, generate_workout_plan

load_dotenv()

# ─── App Setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///fitness_buddy.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WTF_CSRF_ENABLED"] = True

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Context Processors ──────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return {"unread_count": unread_count, "now": datetime.utcnow()}


# ─── Landing Page ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ─── Auth ────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("signup.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("signup.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("signup.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Welcome notification
        notif = Notification(
            user_id=user.id,
            title="Welcome to Fitness Buddy! 🎉",
            message="Your account is ready. Set up your fitness profile to get personalised recommendations.",
            type="general",
        )
        db.session.add(notif)
        db.session.commit()

        login_user(user)
        flash("Account created! Let's set up your profile.", "success")
        return redirect(url_for("profile"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 💪", "success")
            return redirect(next_page or url_for("dashboard"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ─── Dashboard ───────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    profile = current_user.profile
    today = date.today()

    # Today's habit log
    habit = HabitLog.query.filter_by(user_id=current_user.id, log_date=today).first()

    # Recent weight logs
    weight_logs = (
        WeightLog.query.filter_by(user_id=current_user.id)
        .order_by(WeightLog.log_date.desc())
        .limit(7)
        .all()
    )

    # Recent notifications
    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    # Weekly habit summary
    from sqlalchemy import func
    from datetime import timedelta
    week_ago = today - timedelta(days=6)
    weekly_habits = (
        HabitLog.query.filter(
            HabitLog.user_id == current_user.id,
            HabitLog.log_date >= week_ago,
        )
        .order_by(HabitLog.log_date)
        .all()
    )

    return render_template(
        "dashboard.html",
        profile=profile,
        habit=habit,
        weight_logs=weight_logs,
        notifications=notifications,
        weekly_habits=weekly_habits,
        today=today,
    )


# ─── Fitness Profile ─────────────────────────────────────────────────────────
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    p = current_user.profile

    if request.method == "POST":
        if p is None:
            p = FitnessProfile(user_id=current_user.id)
            db.session.add(p)

        p.name = request.form.get("name", "").strip()
        p.age = int(request.form.get("age") or 0) or None
        p.gender = request.form.get("gender")
        p.height_cm = float(request.form.get("height_cm") or 0) or None
        p.weight_kg = float(request.form.get("weight_kg") or 0) or None
        p.goal = request.form.get("goal")
        p.activity_level = request.form.get("activity_level")
        db.session.commit()

        # Log weight
        if p.weight_kg:
            w = WeightLog(user_id=current_user.id, weight_kg=p.weight_kg, bmi=p.bmi, log_date=date.today())
            db.session.add(w)
            db.session.commit()

        flash("Profile updated! ✅", "success")
        return redirect(url_for("dashboard"))

    return render_template("profile.html", profile=p)


# ─── AI Chatbot ──────────────────────────────────────────────────────────────
@app.route("/chatbot")
@login_required
def chatbot():
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    messages = list(reversed(messages))
    return render_template("chatbot.html", messages=messages)


@app.route("/chatbot/send", methods=["POST"])
@login_required
def chatbot_send():
    data = request.get_json()
    user_message = (data or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Save user message
    db.session.add(ChatMessage(user_id=current_user.id, role="user", content=user_message))
    db.session.commit()

    # Build history
    history_rows = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(history_rows)]

    # Build profile context string
    profile_str = ""
    p = current_user.profile
    if p:
        profile_str = (
            f"Name: {p.name}, Age: {p.age}, Gender: {p.gender}, "
            f"Height: {p.height_cm} cm, Weight: {p.weight_kg} kg, "
            f"BMI: {p.bmi} ({p.bmi_category}), Goal: {p.goal}, "
            f"Activity Level: {p.activity_level}, TDEE: {p.tdee} kcal/day"
        )

    ai_response = chat_with_granite(user_message, history, profile_str)

    # Save AI response
    db.session.add(ChatMessage(user_id=current_user.id, role="assistant", content=ai_response))
    db.session.commit()

    return jsonify({"response": ai_response})


@app.route("/chatbot/clear", methods=["POST"])
@login_required
def chatbot_clear():
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})


# ─── Meal Planner ────────────────────────────────────────────────────────────
@app.route("/meal-planner", methods=["GET", "POST"])
@login_required
def meal_planner():
    today = date.today()
    plan = MealPlan.query.filter_by(user_id=current_user.id, plan_date=today).first()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "ai_generate":
            if not current_user.profile:
                flash("Please complete your fitness profile first.", "warning")
                return redirect(url_for("profile"))
            ai_data = generate_meal_plan(current_user.profile)
            if "error" in ai_data:
                flash(f"AI generation failed: {ai_data['error']}", "danger")
            else:
                if plan is None:
                    plan = MealPlan(user_id=current_user.id, plan_date=today)
                    db.session.add(plan)
                plan.breakfast = ai_data.get("breakfast", "")
                plan.lunch = ai_data.get("lunch", "")
                plan.dinner = ai_data.get("dinner", "")
                plan.snacks = ai_data.get("snacks", "")
                plan.total_calories = ai_data.get("total_calories", 0)
                plan.water_target_ml = ai_data.get("water_target_ml", 2500)
                plan.ai_generated = True
                db.session.commit()
                flash("AI meal plan generated! 🍽️", "success")
        else:
            if plan is None:
                plan = MealPlan(user_id=current_user.id, plan_date=today)
                db.session.add(plan)
            plan.breakfast = request.form.get("breakfast", "")
            plan.lunch = request.form.get("lunch", "")
            plan.dinner = request.form.get("dinner", "")
            plan.snacks = request.form.get("snacks", "")
            plan.total_calories = int(request.form.get("total_calories") or 0)
            plan.water_target_ml = int(request.form.get("water_target_ml") or 2500)
            plan.ai_generated = False
            db.session.commit()
            flash("Meal plan saved! 💾", "success")
        return redirect(url_for("meal_planner"))

    return render_template("meal_planner.html", plan=plan, today=today)


# ─── BMI Calculator ──────────────────────────────────────────────────────────
@app.route("/bmi-calculator", methods=["GET", "POST"])
@login_required
def bmi_calculator():
    result = None
    if request.method == "POST":
        try:
            height_cm = float(request.form["height_cm"])
            weight_kg = float(request.form["weight_kg"])
            age = int(request.form.get("age") or 0)
            gender = request.form.get("gender", "")
            h = height_cm / 100
            bmi = round(weight_kg / (h * h), 1)

            if bmi < 18.5:
                category, color = "Underweight", "info"
            elif bmi < 25:
                category, color = "Normal Weight", "success"
            elif bmi < 30:
                category, color = "Overweight", "warning"
            else:
                category, color = "Obese", "danger"

            # BMR
            if gender.lower() == "male":
                bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5) if age else None
            else:
                bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161) if age else None

            result = {
                "bmi": bmi, "category": category, "color": color,
                "height_cm": height_cm, "weight_kg": weight_kg, "bmr": bmr,
                "ideal_weight_min": round(18.5 * h * h, 1),
                "ideal_weight_max": round(24.9 * h * h, 1),
            }
        except (ValueError, KeyError):
            flash("Please enter valid numbers.", "danger")

    # Pre-fill from profile
    p = current_user.profile
    return render_template("bmi_calculator.html", result=result, profile=p)


# ─── Habit Tracker ───────────────────────────────────────────────────────────
@app.route("/habits", methods=["GET", "POST"])
@login_required
def habits():
    today = date.today()
    log = HabitLog.query.filter_by(user_id=current_user.id, log_date=today).first()

    if request.method == "POST":
        if log is None:
            log = HabitLog(user_id=current_user.id, log_date=today)
            db.session.add(log)
        log.water_glasses = int(request.form.get("water_glasses") or 0)
        log.sleep_hours = float(request.form.get("sleep_hours") or 0)
        log.steps = int(request.form.get("steps") or 0)
        log.workout_done = bool(request.form.get("workout_done"))
        log.notes = request.form.get("notes", "")
        db.session.commit()
        flash("Today's habits logged! 🌟", "success")
        return redirect(url_for("habits"))

    # Last 7 days
    from datetime import timedelta
    week_logs = (
        HabitLog.query.filter(
            HabitLog.user_id == current_user.id,
            HabitLog.log_date >= today - timedelta(days=6),
        )
        .order_by(HabitLog.log_date)
        .all()
    )
    return render_template("habits.html", log=log, week_logs=week_logs, today=today)


# ─── Progress Dashboard ──────────────────────────────────────────────────────
@app.route("/progress")
@login_required
def progress():
    weight_logs = (
        WeightLog.query.filter_by(user_id=current_user.id)
        .order_by(WeightLog.log_date)
        .all()
    )
    habit_logs = (
        HabitLog.query.filter_by(user_id=current_user.id)
        .order_by(HabitLog.log_date)
        .all()
    )
    meal_logs = (
        MealPlan.query.filter_by(user_id=current_user.id)
        .order_by(MealPlan.plan_date.desc())
        .limit(14)
        .all()
    )

    # Serialisable chart data
    weight_chart = [{"date": str(w.log_date), "weight": w.weight_kg, "bmi": w.bmi} for w in weight_logs]
    habit_chart = [
        {
            "date": str(h.log_date),
            "water": h.water_glasses,
            "sleep": h.sleep_hours,
            "steps": h.steps,
            "workout": 1 if h.workout_done else 0,
        }
        for h in habit_logs
    ]

    return render_template(
        "progress.html",
        weight_logs=weight_logs,
        habit_logs=habit_logs,
        meal_logs=meal_logs,
        weight_chart=weight_chart,
        habit_chart=habit_chart,
    )


# ─── Workout Plan ────────────────────────────────────────────────────────────
@app.route("/workout-plan")
@login_required
def workout_plan():
    if not current_user.profile:
        flash("Please complete your fitness profile first.", "warning")
        return redirect(url_for("profile"))
    plan = generate_workout_plan(current_user.profile)
    return render_template("workout_plan.html", plan=plan)


# ─── Notifications ───────────────────────────────────────────────────────────
@app.route("/notifications")
@login_required
def notifications():
    notifs = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("notifications.html", notifications=notifs)


@app.route("/notifications/add-reminders", methods=["POST"])
@login_required
def add_reminders():
    reminders = [
        ("💧 Water Reminder", "Time to drink a glass of water! Stay hydrated.", "water"),
        ("🏋️ Workout Reminder", "Don't forget your workout today! Even 30 minutes counts.", "workout"),
        ("😴 Sleep Reminder", "Aim for 7-8 hours of quality sleep tonight.", "sleep"),
    ]
    for title, message, type_ in reminders:
        db.session.add(Notification(user_id=current_user.id, title=title, message=message, type=type_))
    db.session.commit()
    flash("Reminders added! 🔔", "success")
    return redirect(url_for("notifications"))


@app.route("/notifications/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    return jsonify({"status": "ok"})


# ─── Weight Log (AJAX) ───────────────────────────────────────────────────────
@app.route("/log-weight", methods=["POST"])
@login_required
def log_weight():
    data = request.get_json()
    weight = float(data.get("weight_kg", 0))
    if weight <= 0:
        return jsonify({"error": "Invalid weight"}), 400

    p = current_user.profile
    bmi = None
    if p and p.height_cm:
        h = p.height_cm / 100
        bmi = round(weight / (h * h), 1)

    w = WeightLog(user_id=current_user.id, weight_kg=weight, bmi=bmi, log_date=date.today())
    db.session.add(w)
    db.session.commit()
    return jsonify({"status": "ok", "bmi": bmi})


# ─── Init DB ─────────────────────────────────────────────────────────────────
def create_tables():
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    create_tables()
    app.run(
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
    )
