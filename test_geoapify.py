import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEOAPIFY_API_KEY")

if api_key:
    print("Geoapify API key loaded successfully.")
else:
    print("Geoapify API key NOT found.")