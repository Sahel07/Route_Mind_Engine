import os
import time
import httpx
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# =========================================================
# GOOGLE PLACE DETAILS
# =========================================================

def get_place_details(place_id: str):

    if not API_KEY:
        return {
            "success": False,
            "message": "GOOGLE_MAPS_API_KEY not found in .env file."
        }

    if not place_id:
        return {
            "success": False,
            "message": "Place ID is required."
        }

    url = (
        f"https://places.googleapis.com/v1/places/"
        f"{place_id}"
    )

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,

        # -------------------------------------------------
        # Fields we want from Google
        # -------------------------------------------------

        "X-Goog-FieldMask": (
            "id,"
            "displayName,"
            "formattedAddress,"
            "location,"
            "rating,"
            "userRatingCount,"
            "nationalPhoneNumber,"
            "websiteUri,"
            "regularOpeningHours"
        )
    }

    try:

        print(
            f"\n[Google Details] "
            f"Fetching place details..."
        )

        # -------------------------------------------------
        # REQUEST WITH 429 RETRY / BACKOFF
        # -------------------------------------------------
        max_retries = 3
        delays = [2, 5, 10]

        for attempt in range(max_retries + 1):

            response = httpx.get(
                url,
                headers=headers,
                timeout=30
            )

            print(
                f"[Google Details] "
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                break

            if response.status_code == 429 and attempt < max_retries:

                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        wait_seconds = max(1, int(float(retry_after)))
                    except ValueError:
                        wait_seconds = delays[attempt]
                else:
                    wait_seconds = delays[attempt]

                print(
                    f"[Google Details] Rate limited (429). "
                    f"Retrying in {wait_seconds}s "
                    f"({attempt + 1}/{max_retries})..."
                )

                time.sleep(wait_seconds)
                continue

            return {
                "success": False,
                "status_code": response.status_code,
                "message": (
                    "Google Place Details API error:\n"
                    f"{response.text}"
                )
            }

        # -------------------------------------------------
        # JSON RESPONSE
        # -------------------------------------------------

        data = response.json()

        # -------------------------------------------------
        # RETURN DATA
        # -------------------------------------------------

        return {
            "success": True,
            "data": data
        }

    except httpx.TimeoutException:

        return {
            "success": False,
            "message": (
                "Google Place Details request "
                "timed out."
            )
        }

    except httpx.RequestError as e:

        return {
            "success": False,
            "message": (
                f"Network error: {str(e)}"
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

    print(
        "\n======================================"
    )

    print(
        " GOOGLE PLACE DETAILS TEST"
    )

    print(
        "======================================"
    )

    # -----------------------------------------------------
    # Fort Aguada Place ID
    # -----------------------------------------------------

    place_id = input(
        "\nEnter Google Place ID: "
    ).strip()

    result = get_place_details(
        place_id
    )

    print(
        "\n======================================"
    )

    if result["success"]:

        print(
            "SUCCESS - PLACE DETAILS FOUND"
        )

        print(
            "======================================"
        )

        data = result["data"]

        print(
            "\nRaw Google Response:"
        )

        print(
            data
        )

        print(
            "\n--------------------------------------"
        )

        print(
            "IMPORTANT FIELDS"
        )

        print(
            "--------------------------------------"
        )

        print(
            "ID:",
            data.get("id")
        )

        print(
            "Name:",
            data.get(
                "displayName",
                {}
            ).get("text")
        )

        print(
            "Address:",
            data.get(
                "formattedAddress"
            )
        )

        print(
            "Rating:",
            data.get(
                "rating"
            )
        )

        print(
            "Review Count:",
            data.get(
                "userRatingCount"
            )
        )

        print(
            "Phone:",
            data.get(
                "nationalPhoneNumber"
            )
        )

        print(
            "Website:",
            data.get(
                "websiteUri"
            )
        )

        print(
            "Opening Hours:",
            data.get(
                "regularOpeningHours"
            )
        )

    else:

        print(
            "FAILED"
        )

        print(
            result.get(
                "message"
            )
        )