import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY")

place = input("Enter Place Name: ")

url = "https://api.geoapify.com/v1/geocode/search"

params = {
    "text": place,
    "apiKey": API_KEY,
    "limit": 5
}

response = httpx.get(url, params=params, timeout=20)

print("\n----------------------------")

if response.status_code != 200:
    print("HTTP Error:", response.status_code)
    print(response.text)
    exit()

data = response.json()

features = data.get("features", [])

if not features:
    print("No location found.")
    exit()

print("Locations found:\n")

for i, feature in enumerate(features, start=1):

    properties = feature.get("properties", {})

    print(f"{i}. {properties.get('formatted')}")
    print(f"   Latitude: {properties.get('lat')}")
    print(f"   Longitude: {properties.get('lon')}")
    print()