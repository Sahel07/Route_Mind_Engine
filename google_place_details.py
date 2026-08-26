import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_place_details(place_id: str):

    if not API_KEY:
        return {
            "success": False,
            "rating": None,
            "review_count": None,
            "website": None,
            "opening_hours": None,
            "phone": None
        }

    if not place_id:
        return {
            "success": False,
            "rating": None,
            "review_count": None,
            "website": None,
            "opening_hours": None,
            "phone": None
        }

    url = (
        "https://places.googleapis.com/v1/"
        f"places/{place_id}"
    )

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,

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

    max_retries = 3
    delays = [2, 5, 10]

    try:

        print(
            f"\n[Google Details] "
            f"Fetching details for {place_id}..."
        )

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

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                return {
                    "success": True,

                    "rating":
                        data.get("rating"),

                    "review_count":
                        data.get("userRatingCount"),

                    "website":
                        data.get("websiteUri"),

                    "opening_hours":
                        data.get("regularOpeningHours"),

                    "phone":
                        data.get("nationalPhoneNumber")
                }

            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            if response.status_code == 429:

                if attempt < max_retries:

                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    if retry_after:

                        try:
                            wait_seconds = max(
                                1,
                                int(float(retry_after))
                            )
                        except ValueError:
                            wait_seconds = delays[attempt]

                    else:
                        wait_seconds = delays[attempt]

                    print(
                        f"[Google Details] "
                        f"Rate limited (429). "
                        f"Retrying in {wait_seconds}s "
                        f"({attempt + 1}/{max_retries})..."
                    )

                    time.sleep(wait_seconds)

                    continue

                print(
                    "[Google Details] "
                    "429 after all retries."
                )

                return {
                    "success": False,
                    "rating": None,
                    "review_count": None,
                    "website": None,
                    "opening_hours": None,
                    "phone": None
                }

            # -------------------------------------------------
            # OTHER GOOGLE ERROR
            # -------------------------------------------------

            print(
                f"[Google Details] "
                f"Failed: {response.status_code}"
            )

            return {
                "success": False,
                "rating": None,
                "review_count": None,
                "website": None,
                "opening_hours": None,
                "phone": None
            }

    except httpx.TimeoutException:

        print(
            "[Google Details] "
            "Request timed out."
        )

    except httpx.RequestError as e:

        print(
            f"[Google Details] "
            f"Network error: {e}"
        )

    except Exception as e:

        print(
            f"[Google Details] "
            f"Error: {e}"
        )

    return {
        "success": False,
        "rating": None,
        "review_count": None,
        "website": None,
        "opening_hours": None,
        "phone": None
    }