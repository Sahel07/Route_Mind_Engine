import httpx


def find_attractions(place_name: str):
    """
    Find attractions/places related to a location
    using the Wikipedia API.
    """

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"tourist attractions in {place_name}",
        "srlimit": 10,
        "format": "json"
    }

    headers = {
        "User-Agent": "RouteMindEngine/1.0 (Educational Project)"
    }

    try:

        response = httpx.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": f"HTTP Error: {response.status_code}"
            }

        data = response.json()

        results = data.get("query", {}).get("search", [])

        if not results:
            return {
                "success": False,
                "message": "No attractions found."
            }

        attractions = []

        for result in results:

            title = result.get("title")

            if title:
                attractions.append(title)

        return {
            "success": True,
            "attractions": attractions
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


if __name__ == "__main__":

    place = input("Enter Place Name: ")

    result = find_attractions(place)

    print("\n----------------------------")

    if result["success"]:

        print("Available Attractions:\n")

        for i, attraction in enumerate(
            result["attractions"],
            start=1
        ):
            print(f"{i}. {attraction}")

    else:

        print(result["message"])