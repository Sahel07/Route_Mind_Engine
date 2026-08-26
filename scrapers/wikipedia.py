import httpx


def fetch_place_history(place_name: str):
    """
    Fetch a short history/summary of a place from Wikipedia.
    Returns a dictionary.
    """

    search_name = place_name.replace(" ", "_")

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_name}"

    try:
        headers = {
         "User-Agent": "RouteMindEngine/1.0 (Educational Project)"
        }
        response = httpx.get(
               url,
               headers=headers,
               timeout=20
          )

        print("Status Code:", response.status_code)

        if response.status_code != 200:
                return {
                "success": False,
                "message": f"HTTP Error: {response.status_code}",
                "response": response.text
                }

        data = response.json()

        return {
            "success": True,
            "title": data.get("title"),
            "summary": data.get("extract"),
            "url": data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page")
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


if __name__ == "__main__":

    place = input("Enter Place Name : ")

    result = fetch_place_history(place)

    print("\n----------------------------")

    if result["success"]:
        print("Title :", result["title"])
        print()
        print(result["summary"])
        print()
        print("Wikipedia :", result["url"])

    else:
        print(result["message"])