import os
import httpx

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    print("Google Maps API key not found in .env")
    exit()


# =========================================================
# GOOGLE PLACES SEARCH
# =========================================================

def find_tourist_places(place_name):

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.types"
        )
    }

    payload = {
        "textQuery": f"tourist attractions in {place_name}",
        "languageCode": "en",
        "maxResultCount": 20
    }

    try:

        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:

            return {
                "success": False,
                "message": (
                    f"Google Places API error: "
                    f"{response.status_code}\n"
                    f"{response.text}"
                )
            }

        data = response.json()

        places = data.get(
            "places",
            []
        )

        if not places:

            return {
                "success": False,
                "message": (
                    f"No tourist places found "
                    f"for '{place_name}'."
                )
            }

        results = []

        for place in places:

            display_name = place.get(
                "displayName",
                {}
            )

            location = place.get(
                "location",
                {}
            )

            results.append({

                "place_id": place.get(
                    "id"
                ),

                "name": display_name.get(
                    "text"
                ),

                "address": place.get(
                    "formattedAddress"
                ),

                "latitude": location.get(
                    "latitude"
                ),

                "longitude": location.get(
                    "longitude"
                ),

                "types": place.get(
                    "types",
                    []
                )
            })

        return {
            "success": True,
            "places": results
        }

    except httpx.TimeoutException:

        return {
            "success": False,
            "message": (
                "Google Places request "
                "timed out."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    place_name = input(
        "Enter Place Name: "
    ).strip()

    if not place_name:

        print(
            "Please enter a place name."
        )

        exit()

    result = find_tourist_places(
        place_name
    )

    print("\n----------------------------")

    if not result["success"]:

        print(
            result["message"]
        )

        exit()

    places = result["places"]

    print(
        f"\nFound {len(places)} "
        f"tourist places for "
        f"{place_name.title()}:\n"
    )

    for index, place in enumerate(
        places,
        start=1
    ):

        print(
            f"{index}. {place['name']}"
        )

        print(
            f"   Address: "
            f"{place['address']}"
        )

        print(
            f"   Latitude: "
            f"{place['latitude']}"
        )

        print(
            f"   Longitude: "
            f"{place['longitude']}"
        )

        print(
            f"   Place ID: "
            f"{place['place_id']}"
        )

        print(
            f"   Types: "
            f"{place['types']}"
        )

        print()