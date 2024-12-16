from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import requests

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

# Database model for workout plans
class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(100), nullable=False)
    fitness_level = db.Column(db.String(50), nullable=False)
    week = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('WorkoutImage', backref='plan', lazy=True)

# Database model for workout images
class WorkoutImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plan.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<WorkoutImage {self.id} - Day {self.day_number}>"

# Initialize the database
with app.app_context():
    db.create_all()

def generate_dalle_image(prompt, day_index, plan_id):
    # Check if the image already exists in the database
    existing_image = WorkoutImage.query.filter_by(plan_id=plan_id, day_number=day_index).first()
    if existing_image:
        print(f"Using existing image for day {day_index}")
        return existing_image.image_path

    try:
        # Generate an image using DALL-E API with a supported size (1024x1024)
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response["data"][0]["url"]

        # Download the image and save it locally
        image_path = f"static/images/plan_{plan_id}_day_{day_index}.jpg"
        image_response = requests.get(image_url)
        with open(image_path, "wb") as f:
            f.write(image_response.content)

        # Save the image path to the database
        new_image = WorkoutImage(plan_id=plan_id, day_number=day_index, image_path=image_path)
        db.session.add(new_image)
        db.session.commit()

        print(f"Generated and saved new image for day {day_index}")
        return image_path
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def home():
    workout_plan = ""
    daily_workouts = []
    image_paths = []
    selected_week = ""
    zipped_data = []

    if request.method == "POST":
        goal = request.form.get("goal")
        fitness_level = request.form.get("fitness_level")
        selected_week = request.form.get("week")

        if not selected_week:
            selected_week = "Week 1"

        # Check if the workout for this week, goal, and fitness level already exists
        existing_plan = WorkoutPlan.query.filter_by(goal=goal, fitness_level=fitness_level, week=selected_week).first()

        if existing_plan:
            workout_plan = existing_plan.content
            plan_id = existing_plan.id
            print(f"Retrieved existing plan for {selected_week}")
        else:
            # Construct a 7-day workout plan prompt with the selected week
            prompt = f"""
            Generate a personalized 7-day workout plan for {selected_week} for someone whose goal is '{goal}' and whose fitness level is '{fitness_level}'. 
            Provide a plan for each day of the week (Day 1 to Day 7), including warm-ups, main exercises, and cool-downs.
            """
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=700
                )
                workout_plan = response["choices"][0]["message"]["content"].strip()

                new_plan = WorkoutPlan(goal=goal, fitness_level=fitness_level, week=selected_week, content=workout_plan)
                db.session.add(new_plan)
                db.session.commit()
                plan_id = new_plan.id
                print(f"Saved new plan for {selected_week}")

            except Exception as e:
                db.session.rollback()
                workout_plan = f"Error: {str(e)}"
                print(f"Error saving plan: {e}")
                return render_template("index.html")

    elif request.method == "GET":
        selected_week = request.args.get("week", "Week 1")
        existing_plan = WorkoutPlan.query.filter_by(week=selected_week).first()

        if existing_plan:
            workout_plan = existing_plan.content
            plan_id = existing_plan.id
            print(f"Retrieved existing plan for {selected_week}")

    # Split the workout plan by days
    if workout_plan:
        daily_workouts = workout_plan.split("Day ")
        daily_workouts = [f"Day {day.strip()}" for day in daily_workouts if day.strip()]
        print(f"Daily workouts: {daily_workouts}")

        # Generate or retrieve images for each day
        for i, day in enumerate(daily_workouts):
            if ':' in day:
                day_prompt = f"An illustration of exercises for {day.split(':', 1)[1].strip()}"
            else:
                day_prompt = "An illustration of a general workout exercise"

            image_path = generate_dalle_image(day_prompt, i + 1, plan_id)
            image_paths.append(image_path)

        # Zip the daily workouts with image paths
        zipped_data = list(zip(daily_workouts, image_paths))

    # Fetch all saved weeks for display in the dropdown
    saved_weeks = WorkoutPlan.query.with_entities(WorkoutPlan.week).distinct().all()
    saved_weeks = [week[0] for week in saved_weeks]

    return render_template("index.html", zipped_data=zipped_data, selected_week=selected_week, saved_weeks=saved_weeks)

@app.route("/wipe", methods=["POST"])
def wipe_database():
    try:
        db.session.query(WorkoutImage).delete()
        db.session.query(WorkoutPlan).delete()
        db.session.commit()
        print("Database wiped successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error wiping database: {e}")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
