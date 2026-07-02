# 💪 Fitness Buddy — AI-Powered Fitness Coach

> A complete web application powered by **IBM Granite** on **IBM Watsonx.ai**, built with Python Flask and Bootstrap 5.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Coach** | IBM Granite chatbot with personalised workout & nutrition advice |
| 🍽️ **Meal Planner** | AI-generated daily meal plans (Indian diet supported) |
| 📊 **BMI Calculator** | BMI, BMR, ideal weight & health insights |
| 🏋️ **Workout Plans** | AI-crafted weekly programs for all fitness levels |
| ✅ **Habit Tracker** | Water, sleep, steps & workout completion |
| 📈 **Progress Dashboard** | Weight, BMI history, calorie & habit charts |
| 🔔 **Smart Notifications** | Workout, water & sleep reminders |
| 🌙 **Dark Mode** | Persistent user preference |
| 📱 **Fully Responsive** | Mobile-first Bootstrap 5 design |
| 🔒 **Secure Auth** | Flask-Login + Bcrypt password hashing |

---

## 🏗️ Project Structure

```
fitness_buddy/
├── app.py              ← Main Flask application & all routes
├── models.py           ← SQLAlchemy database models
├── watsonx_ai.py       ← IBM Watsonx.ai / Granite integration + AGENT_INSTRUCTIONS
├── requirements.txt    ← Python dependencies
├── .env.example        ← Environment variable template
├── .env                ← Your credentials (never commit!)
├── static/
│   ├── css/style.css   ← Custom styles, dark mode, animations
│   └── js/main.js      ← Dark mode, UI interactions, AJAX helpers
└── templates/
    ├── base.html        ← Shared layout (navbar, footer, flash)
    ├── index.html       ← Landing page (hero, features, about, contact)
    ├── login.html       ← Login page
    ├── signup.html      ← Registration page
    ├── dashboard.html   ← Main dashboard with charts
    ├── profile.html     ← Fitness profile setup
    ├── chatbot.html     ← AI coach chat interface
    ├── meal_planner.html← Meal planning + AI generation
    ├── bmi_calculator.html ← BMI calculator with reference table
    ├── habits.html      ← Daily habit tracker with ring charts
    ├── progress.html    ← Progress charts (Chart.js)
    ├── workout_plan.html← AI-generated workout plan
    └── notifications.html ← Notification centre
```

---

## 🚀 Quick Start

### 1. Clone & Navigate

```bash
cd fitness_buddy
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy the example
cp .env.example .env

# Edit .env with your credentials:
#   WATSONX_API_KEY=...
#   WATSONX_PROJECT_ID=...
```

### 5. Run the Application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 IBM Watsonx.ai Credentials

1. Sign in to [IBM Cloud](https://cloud.ibm.com)
2. Create or open a **Watson Machine Learning** service
3. Create a **Watsonx.ai project** at [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
4. Generate an **API Key** from IBM Cloud → Manage → Access (IAM) → API Keys
5. Copy your **Project ID** from the Watsonx.ai project settings
6. Paste both into your `.env` file

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
```

---

## 🤖 AGENT_INSTRUCTIONS — Customise Your AI Coach

Edit [`watsonx_ai.py`](watsonx_ai.py) or your `.env` file to customise the AI coach behaviour:

```env
# Coach personality: motivational | strict | friendly | scientific
COACH_PERSONALITY=motivational

# Workout difficulty: beginner | intermediate | advanced
WORKOUT_DIFFICULTY=intermediate

# Indian diet preference: true | false
INDIAN_DIET_PREFERENCE=true

# Safety rules: true | false
SAFETY_RULES=true

# Motivation style: positive | tough-love | balanced
MOTIVATION_STYLE=balanced
```

### Personality Options

| Value | Description |
|---|---|
| `motivational` | Enthusiastic, energetic, always encouraging |
| `strict` | Disciplined, no-nonsense, pushes limits |
| `friendly` | Warm, supportive best-friend coach |
| `scientific` | Evidence-based, sports science focused |

### Motivation Styles

| Value | Description |
|---|---|
| `positive` | Uplifting, celebrates every small win |
| `tough-love` | Direct, honest, holds you accountable |
| `balanced` | Encouragement mixed with realistic feedback |

---

## 🗄️ Database Models

| Model | Fields |
|---|---|
| `User` | id, username, email, password_hash, created_at |
| `FitnessProfile` | name, age, gender, height_cm, weight_kg, goal, activity_level |
| `HabitLog` | water_glasses, sleep_hours, steps, workout_done, notes, log_date |
| `WeightLog` | weight_kg, bmi, log_date, notes |
| `MealPlan` | breakfast, lunch, dinner, snacks, total_calories, water_target_ml |
| `ChatMessage` | role (user/assistant), content, created_at |
| `Notification` | title, message, type, is_read, created_at |

---

## 🌐 Deployment

### Option A: Gunicorn (Linux/macOS Production)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

### Option B: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t fitness-buddy .
docker run -p 5000:5000 --env-file .env fitness-buddy
```

### Option C: IBM Cloud Code Engine

```bash
# Install IBM Cloud CLI
ibmcloud login
ibmcloud ce project create --name fitness-buddy
ibmcloud ce application create \
  --name fitness-buddy-app \
  --image <your-container-registry>/fitness-buddy:latest \
  --env-from-secret fitness-buddy-secrets \
  --port 5000
```

### Option D: Render / Railway (Free Tiers)

1. Push to GitHub
2. Connect your repo to [Render](https://render.com) or [Railway](https://railway.app)
3. Set environment variables in the dashboard
4. Deploy with `gunicorn app:app`

### Production Checklist

- [ ] Set `FLASK_DEBUG=False`
- [ ] Use a strong `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Switch `DATABASE_URL` to PostgreSQL for production
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up reverse proxy (Nginx / Caddy)
- [ ] Configure proper logging
- [ ] Use environment secrets manager (not plain `.env`)

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** — never stored in plain text
- CSRF protection via **Flask-WTF**
- All routes require authentication via **Flask-Login**
- AI credentials are loaded from environment variables, never hardcoded
- Never commit your `.env` file (it is in `.gitignore`)

---

## 📦 Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `flask` | 3.0.3 | Web framework |
| `flask-sqlalchemy` | 3.1.1 | ORM / database |
| `flask-login` | 0.6.3 | Session management |
| `flask-bcrypt` | 1.0.1 | Password hashing |
| `flask-wtf` | 1.2.1 | CSRF protection |
| `ibm-watsonx-ai` | 1.1.2 | IBM Granite AI integration |
| `python-dotenv` | 1.0.1 | Environment variables |
| `gunicorn` | 22.0.0 | WSGI production server |

Frontend libraries (CDN):
- Bootstrap 5.3
- Bootstrap Icons 1.11
- Chart.js 4.4
- Google Fonts (Inter)

---

## 💡 Usage Tips

1. **Complete your profile first** — the AI coach uses your BMI, age, weight, and goals to personalise every response
2. **Enable Indian diet** via `INDIAN_DIET_PREFERENCE=true` for regional meal suggestions
3. **Use Quick Topics** in the chatbot sidebar for fast AI responses
4. **Log habits daily** to build streaks and track progress charts
5. **Regenerate workout plans** anytime by visiting the Workout Plan page

---

## ⚕️ Disclaimer

AI responses are for informational and motivational purposes only. Always consult a qualified healthcare professional before beginning any new exercise or diet programme, particularly if you have existing health conditions.

---

*Built with ❤️ using IBM Granite on Watsonx.ai*
