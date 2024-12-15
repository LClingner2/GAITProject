import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Set your OpenAI API key here
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_workout(goal, fitness_level):
    # Construct a prompt for generating workouts based on user's goals and fitness level
    prompt = f"""
    Generate a personalized workout plan for someone whose fitness goal is to '{goal}' and whose fitness level is '{fitness_level}'.
    """

    # Make a call to OpenAI
    response = openai.Completion.create(
        engine="text-davinci-003",  # You could use other models as well
        prompt=prompt,
        max_tokens=150
    )
    
    # Extract the text response
    workout_plan = response.choices[0].text.strip()
    return workout_plan

if __name__ == "__main__":
    # Example usage
    user_goal = "build muscle"
    user_fitness_level = "beginner"
    workout_plan = generate_workout(user_goal, user_fitness_level)
    print("Generated Workout Plan:")
    print(workout_plan)
