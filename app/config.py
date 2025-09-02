# app/config.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Simply update the model name here
llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-pro", temperature=0)