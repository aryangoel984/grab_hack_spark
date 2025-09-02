# check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your API key from the .env file
load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("✅ Your API key has access to the following models:")
print("-" * 50)

# List all models and check if they support the 'generateContent' method
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)