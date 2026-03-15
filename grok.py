import os
from groq import Groq

# Initialize the Groq client. 
# By default, it will automatically look for the GROQ_API_KEY environment variable.
# load api key from .env

import dotenv
dotenv.load_dotenv()
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

# Generate a chat completion
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI assistant."
        },
        {
            "role": "user",
            "content": "Explain the importance of fast language models in two sentences."
        }
    ],
    # Specify the model you want to use (e.g., llama-3.3-70b-versatile, mixtral-8x7b-32768)
    model="llama-3.3-70b-versatile",
)

# Print the output
print(chat_completion.choices[0].message.content)