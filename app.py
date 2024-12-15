from flask import Flask, request, render_template
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    workout_plan = ""
    daily_workouts = []
    selected_week = ""

    if request.method == "POST":
        goal = request.form.get("goal")
        fitness_level = request.form.get("fitness_level")
        selected_week = request.form.get("week")

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

            # Split the workout plan by days using "Day X:" as the delimiter
            daily_workouts = workout_plan.split("Day ")
            daily_workouts = [f"Day {day.strip()}" for day in daily_workouts if day.strip()]
        except Exception as e:
            workout_plan = f"Error: {str(e)}"

    return render_template("index.html", daily_workouts=daily_workouts, selected_week=selected_week)

if __name__ == "__main__":
    app.run(debug=True)
