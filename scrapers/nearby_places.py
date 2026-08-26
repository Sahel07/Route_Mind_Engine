import os
import httpx

from dotenv import load_dotenv


# ---------------------------------------------------------
# Import our photo scraper
# ---------------------------------------------------------

try:

    # When imported as a package
    from .photos import fetch_place_photos

except ImportError:

    # When running:
    # python scrapers/nearby_places.py
    from photos import fetch_place_photos


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)


# =========================================================
# GOOGLE PLACES API
# =========================================================

def find_tourist_places(place_name):

    url = (
        "https://places.googleapis.com/v1/"
        "places:searchText"
    )

    headers = {

        "Content-Type":
            "application/json",

        "X-Goog-Api-Key":
            API_KEY,

        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.types"
        )
    }

    payload = {

        "textQuery": (
            f"tourist attractions in "
            f"{place_name}"
        ),

        "languageCode":
            "en",

        "maxResultCount":
            20
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

            name = display_name.get(
                "text"
            )

            latitude = location.get(
                "latitude"
            )

            longitude = location.get(
                "longitude"
            )

            if (
                not name
                or latitude is None
                or longitude is None
            ):

                continue

            results.append({

                "name":
                    name,

                "display_name":
                    name,

                "address":
                    place.get(
                        "formattedAddress"
                    ),

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "place_id":
                    place.get(
                        "id"
                    ),

                "categories":
                    place.get(
                        "types",
                        []
                    ),

                "score":
                    0,

                # Main image
                "image_url":
                    None,

                # All photos
                "photos":
                    [],

                # Google details
                "rating":
                    None,

                "review_count":
                    None,

                "website":
                    None,

                "opening_hours":
                    None,

                # Future use
                "wikidata":
                    None
            })

        if not results:

            return {

                "success": False,

                "message": (
                    "Google returned places, "
                    "but no usable tourist places "
                    "were found."
                )
            }

        return {

            "success":
                True,

            "selected_location":
                place_name,

            "places":
                results
        }

    except httpx.TimeoutException:

        return {

            "success":
                False,

            "message": (
                "Google Places request "
                "timed out. "
                "Please try again."
            )
        }

    except httpx.RequestError as e:

        return {

            "success":
                False,

            "message": (
                f"Network error: {str(e)}"
            )
        }

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)
        }


# =========================================================
# GOOGLE PLACE DETAILS
# =========================================================

def get_place_details(place_id):
    """
    Fetch additional Google details for one place.

    Details fetched:

        rating
        review_count
        website
        opening_hours
    """

    if not place_id:

        return {

            "success":
                False,

            "rating":
                None,

            "review_count":
                None,

            "website":
                None,

            "opening_hours":
                None
        }

    url = (
        "https://places.googleapis.com/v1/"
        f"places/{place_id}"
    )

    headers = {

        "Content-Type":
            "application/json",

        "X-Goog-Api-Key":
            API_KEY,

        "X-Goog-FieldMask": (
            "id,"
            "displayName,"
            "formattedAddress,"
            "location,"
            "rating,"
            "userRatingCount,"
            "websiteUri,"
            "regularOpeningHours"
        )
    }

    try:

        response = httpx.get(

            url,

            headers=headers,

            timeout=20
        )

        if response.status_code != 200:

            print(
                f"[Google Details] "
                f"Failed for {place_id}: "
                f"{response.status_code}"
            )

            return {

                "success":
                    False,

                "rating":
                    None,

                "review_count":
                    None,

                "website":
                    None,

                "opening_hours":
                    None
            }

        data = response.json()

        return {

            "success":
                True,

            "rating":
                data.get(
                    "rating"
                ),

            "review_count":
                data.get(
                    "userRatingCount"
                ),

            "website":
                data.get(
                    "websiteUri"
                ),

            "opening_hours":
                data.get(
                    "regularOpeningHours"
                )
        }

    except httpx.TimeoutException:

        print(
            f"[Google Details] "
            f"Timeout for {place_id}"
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

        "success":
            False,

        "rating":
            None,

        "review_count":
            None,

        "website":
            None,

        "opening_hours":
            None
    }


# =========================================================
# MAIN FUNCTION USED BY ROUTEMIND
# =========================================================

def find_nearby_places(
    place_name: str
):

    """
    Find tourist attractions for any location.

    Google Places is used to discover attractions.

    Wikimedia Commons is then used to find photos.

    Google Place Details is then used to fetch:

        - rating
        - review count
        - website
        - opening hours
    """

    # -----------------------------------------------------
    # Check API key
    # -----------------------------------------------------

    if not API_KEY:

        return {

            "success":
                False,

            "message": (
                "GOOGLE_MAPS_API_KEY not found "
                "in .env file."
            )
        }

    # -----------------------------------------------------
    # Validate location
    # -----------------------------------------------------

    if (
        not place_name
        or not place_name.strip()
    ):

        return {

            "success":
                False,

            "message": (
                "Please enter a valid "
                "place name."
            )
        }

    place_name = place_name.strip()

    print(
        f"\n[Google Places] "
        f"Searching tourist attractions in "
        f"{place_name}..."
    )

    # =====================================================
    # STEP 1: GET TOURIST PLACES
    # =====================================================

    result = find_tourist_places(
        place_name
    )

    if not result["success"]:

        return result

    places = result["places"]


    # =====================================================
    # STEP 2: REMOVE OBVIOUS NON-ATTRACTIONS
    # =====================================================

    excluded_words = [

        "tourist information",

        "tourist office",

        "booking office",

        "travel agency",

        "tour agency",

        "restaurant",

        "hotel",

        "hostel",

        "shop",

        "store",

        "parking"
    ]

    filtered_places = []

    for place in places:

        name_lower = (
            place["name"]
            .lower()
        )

        categories = [

            category.lower()

            for category
            in place["categories"]
        ]

        # -------------------------------------------------
        # Remove obvious business/service results
        # -------------------------------------------------

        if any(

            word in name_lower

            for word in excluded_words

        ):

            continue

        if (

            "travel_agency"
            in categories

            or

            "tourist_information_center"
            in categories

            or

            "lodging"
            in categories

        ):

            continue

        filtered_places.append(
            place
        )


    # -----------------------------------------------------
    # If filtering removed everything,
    # keep Google's original results.
    # -----------------------------------------------------

    if filtered_places:

        places = filtered_places


    # =====================================================
    # STEP 3: GIVE SIMPLE ATTRACTION SCORES
    # =====================================================

    attraction_keywords = {

        "tourist_attraction":
            20,

        "historical_landmark":
            25,

        "historical_place":
            25,

        "scenic_spot":
            20,

        "beach":
            20,

        "park":
            10,

        "museum":
            15,

        "church":
            15,

        "temple":
            15,

        "mosque":
            15,

        "fort":
            20,

        "waterfall":
            20,

        "natural_feature":
            20
    }


    for place in places:

        score = 0

        categories = [

            category.lower()

            for category
            in place["categories"]
        ]

        for category in categories:

            for (
                keyword,
                points
            ) in attraction_keywords.items():

                if keyword in category:

                    score += points

        place["score"] = score


    # =====================================================
    # STEP 4: SORT BEST ATTRACTIONS FIRST
    # =====================================================

    places.sort(

        key=lambda place:
            place["score"],

        reverse=True
    )


    # =====================================================
    # STEP 5: FETCH PHOTOS
    # =====================================================

    print(
        "\n[Photos] "
        "Searching photos for attractions..."
    )

    for index, place in enumerate(

        places,

        start=1

    ):

        print(

            f"\n[{index}/{len(places)}] "
            f"{place['name']}"
        )

        try:

            photo_result = fetch_place_photos(

                place_name=
                    place["name"],

                location_name=
                    place_name
            )

            if photo_result["success"]:

                photos = (
                    photo_result.get(
                        "photos",
                        []
                    )
                )

                place["photos"] = photos

                # -------------------------------------------------
                # First photo becomes main image
                # -------------------------------------------------

                if photos:

                    place["image_url"] = (
                        photos[0]
                    )

                    print(

                        f"  ✓ "
                        f"{len(photos)} "
                        f"photos found"
                    )

                else:

                    print(
                        "  - No photos found"
                    )

            else:

                place["photos"] = []

                place["image_url"] = None

                print(
                    "  - No photos found"
                )

        except Exception as e:

            # -------------------------------------------------
            # IMPORTANT:
            # One attraction failing should NOT
            # break the entire search.
            # -------------------------------------------------

            place["photos"] = []

            place["image_url"] = None

            print(

                f"  - Photo search failed: "
                f"{str(e)}"
            )


    # =====================================================
    # STEP 6: FETCH GOOGLE PLACE DETAILS
    # =====================================================

    print(
        "\n[Google Details] "
        "Fetching ratings, reviews, websites "
        "and opening hours..."
    )

    for index, place in enumerate(

        places,

        start=1

    ):

        print(

            f"\n[Details {index}/{len(places)}] "
            f"{place['name']}"
        )

        try:

            details = get_place_details(

                place.get(
                    "place_id"
                )
            )

            if details["success"]:

                place["rating"] = (
                    details.get(
                        "rating"
                    )
                )

                place["review_count"] = (
                    details.get(
                        "review_count"
                    )
                )

                place["website"] = (
                    details.get(
                        "website"
                    )
                )

                place["opening_hours"] = (
                    details.get(
                        "opening_hours"
                    )
                )

                print(

                    f"  ✓ Rating: "
                    f"{place['rating']}"
                )

                print(

                    f"  ✓ Reviews: "
                    f"{place['review_count']}"
                )

                print(

                    f"  ✓ Website: "
                    f"{place['website']}"
                )

                if place["opening_hours"]:

                    print(
                        "  ✓ Opening hours found"
                    )

                else:

                    print(
                        "  - Opening hours unavailable"
                    )

            else:

                print(
                    "  - Google details unavailable"
                )

        except Exception as e:

            print(

                f"  - Details failed: "
                f"{str(e)}"
            )


    # =====================================================
    # STEP 7: FINAL RESULT
    # =====================================================

    return {

        "success":
            True,

        "selected_location":
            result[
                "selected_location"
            ],

        "places":
            places
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    place_name = input(
        "Enter Place Name: "
    ).strip()

    result = find_nearby_places(
        place_name
    )

    print(
        "\n============================"
    )

    if result["success"]:

        print(
            "Selected Location:",
            result[
                "selected_location"
            ]
        )

        print(

            f"\nFound "
            f"{len(result['places'])} "
            f"tourist places:\n"
        )

        for index, place in enumerate(

            result["places"],

            start=1

        ):

            print(

                f"{index}. "
                f"{place['name']}"
            )

            print(

                f"   Address: "
                f"{place['address']}"
            )

            print(

                f"   Score: "
                f"{place['score']}"
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

                f"   Categories: "
                f"{place['categories']}"
            )

            # -------------------------------------------------
            # Google Details
            # -------------------------------------------------

            print(

                f"   Rating: "
                f"{place.get('rating')}"
            )

            print(

                f"   Review Count: "
                f"{place.get('review_count')}"
            )

            print(

                f"   Website: "
                f"{place.get('website')}"
            )

            # -------------------------------------------------
            # Opening Hours
            # -------------------------------------------------

            opening_hours = place.get(
                "opening_hours"
            )

            if opening_hours:

                print(
                    "   Opening Hours:"
                )

                weekday_descriptions = (
                    opening_hours.get(
                        "weekdayDescriptions",
                        []
                    )
                )

                for day in (
                    weekday_descriptions
                ):

                    print(
                        f"      {day}"
                    )

            else:

                print(
                    "   Opening Hours: "
                    "Not available"
                )

            # -------------------------------------------------
            # Photos
            # -------------------------------------------------

            print(

                f"   Photos: "
                f"{len(place['photos'])}"
            )

            if place["image_url"]:

                print(

                    f"   Main Image: "
                    f"{place['image_url']}"
                )

            else:

                print(
                    "   Main Image: "
                    "Not available"
                )

            print()

    else:

        print(
            result["message"]
        )