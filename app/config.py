# app/config.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini model
# This single instance will be used by all agents
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)