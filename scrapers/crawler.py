from scrapers.wikipedia import fetch_place_history
from scrapers.geocoder import get_coordinates
from scrapers.database_writer import save_place


def crawl_place(place_name, selected_index):
    """
    Complete pipeline:
    1. Fetch history
    2. Fetch coordinates
    3. Save into SQLite
    """

    print("\nFetching Wikipedia history...")

    history = fetch_place_history(place_name)

    if not history["success"]:
        return {
            "success": False,
            "message": history["message"]
        }

    print("✓ History fetched")

    print("\nFetching coordinates...")

    geo = get_coordinates(place_name)

    if not geo["success"]:
        return {
            "success": False,
            "message": geo["message"]
        }

    print("✓ Coordinates fetched")

    # Check if selected index is valid
    if selected_index < 0 or selected_index >= len(geo["locations"]):
        return {
            "success": False,
            "message": "Invalid location selected."
        }

    selected = geo["locations"][selected_index]

    print("\nSaving into database...")

    result = save_place(
        name=selected["display_name"],
        latitude=selected["latitude"],
        longitude=selected["longitude"],
        history_summary=history["summary"],
        realness_status="Unknown"
    )

    return result


if __name__ == "__main__":

    place = input("Enter Place Name: ")

    geo = get_coordinates(place)

    if not geo["success"]:
        print(geo["message"])
        exit()

    print("\nAvailable Locations:\n")

    for i, location in enumerate(geo["locations"], start=1):
        print(f"{i}. {location['display_name']}")

    while True:
        try:
            choice = int(input("\nSelect a location: "))

            if 1 <= choice <= len(geo["locations"]):
                break

            print("Invalid choice.")

        except ValueError:
            print("Please enter a valid number.")

    result = crawl_place(place, choice - 1)

    print("\n----------------------------")
    print(result["message"])