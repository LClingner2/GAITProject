from flask import Flask, request, render_template
import openai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET", "POST"])
def home():
    workout_plan = ""
    if request.method == "POST":
        goal = request.form.get("goal")
        fitness_level = request.form.get("fitness_level")

        # Make a call to OpenAI to generate the workout
        prompt = f"Generate a personalized workout plan for someone whose goal is '{goal}' and whose fitness level is '{fitness_level}'."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        
        workout_plan = response.choices[0].text.strip()

    return render_template("index.html", workout_plan=workout_plan)

if __name__ == "__main__":
    app.run(debug=True)
