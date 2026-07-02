from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("FitnessProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    habits = db.relationship("HabitLog", backref="user", cascade="all, delete-orphan")
    weight_logs = db.relationship("WeightLog", backref="user", cascade="all, delete-orphan")
    meal_plans = db.relationship("MealPlan", backref="user", cascade="all, delete-orphan")
    chat_messages = db.relationship("ChatMessage", backref="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class FitnessProfile(db.Model):
    __tablename__ = "fitness_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    goal = db.Column(db.String(50))          # Weight Loss | Weight Gain | Muscle Gain | Maintain Fitness
    activity_level = db.Column(db.String(50)) # Sedentary | Lightly Active | Moderately Active | Very Active
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    @property
    def bmi_category(self):
        b = self.bmi
        if b is None:
            return "Unknown"
        if b < 18.5:
            return "Underweight"
        elif b < 25:
            return "Normal"
        elif b < 30:
            return "Overweight"
        return "Obese"

    @property
    def tdee(self):
        """Total Daily Energy Expenditure (Mifflin-St Jeor)."""
        if not (self.weight_kg and self.height_cm and self.age and self.gender):
            return None
        if self.gender.lower() == "male":
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161
        multipliers = {
            "Sedentary": 1.2,
            "Lightly Active": 1.375,
            "Moderately Active": 1.55,
            "Very Active": 1.725,
        }
        return round(bmr * multipliers.get(self.activity_level, 1.2))


class HabitLog(db.Model):
    __tablename__ = "habit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    water_glasses = db.Column(db.Integer, default=0)
    sleep_hours = db.Column(db.Float, default=0.0)
    steps = db.Column(db.Integer, default=0)
    workout_done = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def water_ml(self):
        return self.water_glasses * 250


class WeightLog(db.Model):
    __tablename__ = "weight_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    weight_kg = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MealPlan(db.Model):
    __tablename__ = "meal_plans"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_date = db.Column(db.Date, default=date.today)
    breakfast = db.Column(db.Text)
    lunch = db.Column(db.Text)
    dinner = db.Column(db.Text)
    snacks = db.Column(db.Text)
    total_calories = db.Column(db.Integer)
    water_target_ml = db.Column(db.Integer, default=2500)
    ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(10))   # user | assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    type = db.Column(db.String(30))   # workout | water | sleep | general
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
