import httpx


def get_coordinates(place_name: str):
    """
    Fetch multiple matching locations using
    OpenStreetMap Nominatim API.

    FIX: now also returns "boundingbox" for each location.
    Nominatim gives this for free on every result - it's the
    real geographic rectangle of the place (e.g. the actual
    extent of Goa state, not just its center point). This is
    what lets nearby_places.py search the WHOLE region instead
    of a small circle around one dot, without needing a
    different geocoding provider.
    """

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": "RouteMindEngine/1.0 (Educational Project)"
    }

    params = {
        "q": place_name,
        "format": "json",
        "limit": 5
    }

    try:

        response = httpx.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": f"HTTP Error: {response.status_code}"
            }

        data = response.json()

        if not data:
            return {
                "success": False,
                "message": "Location not found."
            }

        locations = []

        for location in data:

            # boundingbox from Nominatim is
            # [south_lat, north_lat, west_lon, east_lon]
            # as strings - convert to floats up front so
            # callers don't have to.
            raw_bbox = location.get("boundingbox")

            bbox = None

            if raw_bbox and len(raw_bbox) == 4:
                bbox = {
                    "south": float(raw_bbox[0]),
                    "north": float(raw_bbox[1]),
                    "west": float(raw_bbox[2]),
                    "east": float(raw_bbox[3]),
                }

            locations.append({
                "display_name": location["display_name"],
                "latitude": float(location["lat"]),
                "longitude": float(location["lon"]),
                "boundingbox": bbox,
                "place_type": location.get("type"),       # e.g. "administrative"
                "place_class": location.get("class"),     # e.g. "boundary"
            })

        return {
            "success": True,
            "locations": locations
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


if __name__ == "__main__":

    place = input("Enter Place Name : ")

    result = get_coordinates(place)

    if result["success"]:

        print("\nAvailable Locations:\n")

        for i, location in enumerate(result["locations"], start=1):
            print(f"{i}. {location['display_name']}")

        while True:
            try:
                choice = int(input("\nSelect a location (1-5): "))

                if 1 <= choice <= len(result["locations"]):
                    break

                print("Invalid choice. Try again.")

            except ValueError:
                print("Please enter a valid number.")

        selected = result["locations"][choice - 1]

        print("\n----------------------------")
        print("Selected Location")
        print("----------------------------")
        print("Latitude    :", selected["latitude"])
        print("Longitude   :", selected["longitude"])
        print("Location    :", selected["display_name"])
        print("Bounding box:", selected["boundingbox"])

    else:
        print(result["message"])