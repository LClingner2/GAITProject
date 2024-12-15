from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workouts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(100), nullable=False)
    fitness_level = db.Column(db.String(50), nullable=False)
    week = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkoutPlan {self.id} - {self.week}>"

# Initialize the database
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():
    workout_plan = ""
    daily_workouts = []
    selected_week = ""

    if request.method == "POST":
        goal = request.form.get("goal")
        fitness_level = request.form.get("fitness_level")
        selected_week = request.form.get("week")

        # Ensure selected_week has a default value
        if not selected_week:
            selected_week = "Week 1"

        # Check if the workout for this week, goal, and fitness level already exists
        existing_plan = WorkoutPlan.query.filter_by(goal=goal, fitness_level=fitness_level, week=selected_week).first()

        if existing_plan:
            workout_plan = existing_plan.content
        else:
            # Construct a 7-day workout plan prompt with the selected week
            prompt = f"""
            Generate a personalized 7-day workout plan for {selected_week} for someone whose goal is '{goal}' and whose fitness level is '{fitness_level}'. 
            Provide a plan for each day of the week (Day 1 to Day 7), including warm-ups, main exercises, and cool-downs.
            """
            try:
                # Use ChatCompletion for chat-based models
                response = openai.ChatCompletion.create(
                    model="gpt-4",  # Or "gpt-4"
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=700  # Ensure sufficient space for detailed plans
                )
                # Extract the generated workout plan
                workout_plan = response["choices"][0]["message"]["content"].strip()

                # Save the workout plan to the database
                new_plan = WorkoutPlan(goal=goal, fitness_level=fitness_level, week=selected_week, content=workout_plan)
                db.session.add(new_plan)
                db.session.commit()

            except Exception as e:
                db.session.rollback()  # Roll back the session in case of an error
                workout_plan = f"Error: {str(e)}"

        # Split the workout plan by days using "Day X:" as the delimiter
        daily_workouts = workout_plan.split("Day ")
        daily_workouts = [f"Day {day.strip()}" for day in daily_workouts if day.strip()]

    # Fetch all saved weeks for display in the dropdown
    saved_weeks = WorkoutPlan.query.with_entities(WorkoutPlan.week).distinct().all()
    saved_weeks = [week[0] for week in saved_weeks]

    return render_template("index.html", daily_workouts=daily_workouts, selected_week=selected_week, saved_weeks=saved_weeks)

@app.route("/view", methods=["GET"])
def view_week():
    week = request.args.get("week")
    plan = WorkoutPlan.query.filter_by(week=week).first()
    daily_workouts = []

    if plan:
        # Split the workout plan by days using "Day X:" as the delimiter
        daily_workouts = plan.content.split("Day ")
        daily_workouts = [f"Day {day.strip()}" for day in daily_workouts if day.strip()]

    # Fetch all saved weeks for display in the dropdown
    saved_weeks = WorkoutPlan.query.with_entities(WorkoutPlan.week).distinct().all()
    saved_weeks = [week[0] for week in saved_weeks]

    return render_template("index.html", daily_workouts=daily_workouts, selected_week=week, saved_weeks=saved_weeks)

@app.route("/wipe", methods=["POST"])
def wipe_database():
    try:
        # Delete all records from the WorkoutPlan table
        db.session.query(WorkoutPlan).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
