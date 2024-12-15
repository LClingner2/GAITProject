import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_workout(goal, fitness_level):
    """
    Generate a 7-day personalized workout plan based on the user's goals and fitness level.
    """
    # Construct a prompt for generating a 7-day workout plan
    prompt = f"""
    Generate a personalized 7-day workout plan for someone whose fitness goal is to '{goal}' and whose fitness level is '{fitness_level}'. 
    Provide a plan for each day of the week (Day 1 to Day 7), including warm-ups, main exercises, and cool-downs.
    """

    try:
        # Use ChatCompletion for chat-based models
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Or "gpt-4" if available
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500  # Increase token limit to ensure the response is long enough
        )
        # Extract the generated workout plan
        workout_plan = response["choices"][0]["message"]["content"].strip()
        return workout_plan
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example usage
    user_goal = "build muscle"
    user_fitness_level = "beginner"
    workout_plan = generate_workout(user_goal, user_fitness_level)
    print("Generated Workout Plan:")
    print(workout_plan)
