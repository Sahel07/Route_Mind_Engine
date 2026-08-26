import os
import httpx

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

PLACE_ID = "ChIJa72MxnXBvzsRHHtpszB2g6M"


url = (
    f"https://places.googleapis.com/v1/places/"
    f"{PLACE_ID}"
)

headers = {
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": (
        "id,"
        "displayName,"
        "formattedAddress,"
        "location,"
        "rating,"
        "websiteUri,"
        "photos"
    )
}


response = httpx.get(
    url,
    headers=headers,
    timeout=30
)


print("\n----------------------------")


if response.status_code != 200:

    print(
        "HTTP Error:",
        response.status_code
    )

    print(response.text)

    exit()


data = response.json()


print(
    "Place:",
    data.get("displayName", {}).get("text")
)

print(
    "Address:",
    data.get("formattedAddress")
)

print(
    "Rating:",
    data.get("rating")
)

print(
    "Website:",
    data.get("websiteUri")
)


photos = data.get(
    "photos",
    []
)


print(
    f"\nPhotos returned: "
    f"{len(photos)}"
)


for index, photo in enumerate(
    photos[:5],
    start=1
):

    print(
        f"\nPhoto {index}:"
    )

    print(
        "Name:",
        photo.get("name")
    )

    print(
        "Width:",
        photo.get("widthPx")
    )

    print(
        "Height:",
        photo.get("heightPx")
    )