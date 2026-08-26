import httpx
import re
import time


# =========================================================
# WIKIMEDIA COMMONS PHOTO SEARCH
# =========================================================

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "RouteMindEngine/1.0 "
        "(Educational Project; contact: routemind@example.com)"
    )
}


def search_wikimedia(query, max_results=30, retries=3):
    """
    Search Wikimedia Commons for image files.

    Includes retry handling for temporary Wikimedia
    errors such as 429 and 5xx responses.
    """

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": min(max_results, 50),

        "prop": "imageinfo",
        "iiprop": "url",

        "format": "json",
        "formatversion": 2
    }

    for attempt in range(1, retries + 1):

        try:

            response = httpx.get(
                WIKIMEDIA_API,
                params=params,
                headers=HEADERS,
                timeout=20
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                pages = data.get("query", {}).get(
                    "pages", []
                )

                results = []

                for page in pages:

                    title = page.get(
                        "title",
                        ""
                    )

                    image_info = page.get(
                        "imageinfo",
                        []
                    )

                    if not image_info:
                        continue

                    image_url = image_info[0].get(
                        "url"
                    )

                    if not image_url:
                        continue

                    # -----------------------------------------
                    # ONLY REAL IMAGE FILES
                    # -----------------------------------------

                    image_url_without_query = (
                        image_url
                        .split("?")[0]
                        .lower()
                    )

                    valid_extensions = (
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".webp"
                    )

                    if not image_url_without_query.endswith(
                        valid_extensions
                    ):
                        continue

                    # -----------------------------------------
                    # AVOID DUPLICATES
                    # -----------------------------------------

                    if any(
                        item["url"] == image_url
                        for item in results
                    ):
                        continue

                    results.append({
                        "title": title,
                        "url": image_url
                    })

                    if len(results) >= max_results:
                        break

                return results

            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            if response.status_code == 429:

                print(
                    f"[Wikimedia] Rate limited "
                    f"(429). Retry {attempt}/{retries}..."
                )

                time.sleep(2 * attempt)
                continue

            # -------------------------------------------------
            # SERVER ERRORS
            # -------------------------------------------------

            if response.status_code in (
                500,
                502,
                503,
                504
            ):

                print(
                    f"[Wikimedia] Server error "
                    f"{response.status_code}. "
                    f"Retry {attempt}/{retries}..."
                )

                time.sleep(1.5 * attempt)
                continue

            # -------------------------------------------------
            # OTHER HTTP ERROR
            # -------------------------------------------------

            print(
                f"[Wikimedia] HTTP error: "
                f"{response.status_code}"
            )

            return []

        except httpx.TimeoutException:

            print(
                f"[Wikimedia] Timeout. "
                f"Retry {attempt}/{retries}..."
            )

            time.sleep(attempt)

        except httpx.RequestError as e:

            print(
                f"[Wikimedia] Network error: "
                f"{e}"
            )

            time.sleep(attempt)

        except Exception as e:

            print(
                f"[Wikimedia] Unexpected error: "
                f"{e}"
            )

            return []

    return []


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    # Remove Wikimedia prefix
    text = text.replace(
        "file:",
        ""
    )

    # Replace punctuation with spaces
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# =========================================================
# CREATE SEARCH TOKENS
# =========================================================

def get_tokens(text):

    normalized = normalize_text(text)

    if not normalized:
        return []

    stop_words = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "at",
        "on",
        "and",
        "goa",
        "india"
    }

    return [
        word
        for word in normalized.split()
        if word not in stop_words
        and len(word) > 2
    ]


# =========================================================
# SCORE WIKIMEDIA PHOTO
# =========================================================

def score_photo(
    title,
    place_name,
    location_name=""
):

    title_normalized = normalize_text(
        title
    )

    place_normalized = normalize_text(
        place_name
    )

    location_normalized = normalize_text(
        location_name
    )

    score = 0

    # ---------------------------------------------------------
    # EXACT ATTRACTION NAME
    # ---------------------------------------------------------

    if (
        place_normalized
        and place_normalized
        in title_normalized
    ):

        score += 100

    # ---------------------------------------------------------
    # INDIVIDUAL ATTRACTION WORDS
    # ---------------------------------------------------------

    place_tokens = get_tokens(
        place_name
    )

    for token in place_tokens:

        if token in title_normalized:

            score += 20

    # ---------------------------------------------------------
    # LOCATION MATCH
    # ---------------------------------------------------------

    location_tokens = get_tokens(
        location_name
    )

    for token in location_tokens:

        if token in title_normalized:

            score += 5

    # ---------------------------------------------------------
    # USEFUL ATTRACTION KEYWORDS
    # ---------------------------------------------------------

    attraction_words = [
        "fort",
        "falls",
        "waterfall",
        "beach",
        "dam",
        "temple",
        "church",
        "museum",
        "palace",
        "park",
        "lake",
        "river",
        "island",
        "lighthouse",
        "monument",
        "bridge",
        "garden",
        "forest"
    ]

    for word in attraction_words:

        if word in place_normalized:

            if word in title_normalized:

                score += 30

    # ---------------------------------------------------------
    # PENALIZE CLEARLY UNRELATED RESULTS
    # ---------------------------------------------------------

    bad_words = [
        "map",
        "location map",
        "route",
        "road",
        "street",
        "railway station",
        "airport",
        "hotel",
        "restaurant",
        "logo",
        "flag",
        "district map",
        "taluka map",
        "village map"
    ]

    for word in bad_words:

        if word in title_normalized:

            score -= 80

    return score


# =========================================================
# BUILD SEARCH QUERIES
# =========================================================

def build_search_queries(
    place_name,
    location_name
):

    queries = []

    place_name = place_name.strip()
    location_name = location_name.strip()

    # ---------------------------------------------------------
    # 1. Exact place + location
    # ---------------------------------------------------------

    if location_name:

        queries.append(
            f'"{place_name}" "{location_name}"'
        )

    # ---------------------------------------------------------
    # 2. Exact place
    # ---------------------------------------------------------

    queries.append(
        f'"{place_name}"'
    )

    # ---------------------------------------------------------
    # 3. Normal place + location
    # ---------------------------------------------------------

    if location_name:

        queries.append(
            f'{place_name} {location_name}'
        )

    # ---------------------------------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------------------------------

    unique_queries = []

    for query in queries:

        if query not in unique_queries:

            unique_queries.append(query)

    return unique_queries


# =========================================================
# FETCH PHOTOS
# =========================================================

def fetch_place_photos(
    place_name: str,
    location_name: str = ""
):

    """
    Fetch relevant photos for a tourist attraction
    from Wikimedia Commons.

    Returns up to 10 relevant photos.
    """

    place_name = place_name.strip()

    location_name = location_name.strip()

    if not place_name:

        return {
            "success": False,
            "message": "Attraction name is required.",
            "photos": []
        }

    # ---------------------------------------------------------
    # CREATE SEARCH QUERIES
    # ---------------------------------------------------------

    queries = build_search_queries(
        place_name,
        location_name
    )

    # ---------------------------------------------------------
    # SEARCH ALL QUERIES
    # ---------------------------------------------------------

    all_results = []

    for query in queries:

        print(
            f"[Wikimedia] Searching: {query}"
        )

        results = search_wikimedia(
            query,
            max_results=30
        )

        for result in results:

            image_url = result["url"]

            # Avoid duplicate images
            if any(
                item["url"] == image_url
                for item in all_results
            ):
                continue

            all_results.append(result)

        # -----------------------------------------------------
        # SMALL DELAY
        #
        # Prevent sending requests too quickly when many
        # attractions are being processed.
        # -----------------------------------------------------

        time.sleep(0.35)

    # ---------------------------------------------------------
    # NO RESULTS
    # ---------------------------------------------------------

    if not all_results:

        print(
            f"[Wikimedia] No raw results for "
            f"'{place_name}'"
        )

        return {
            "success": False,

            "message": (
                f"No Wikimedia photos found "
                f"for '{place_name}'."
            ),

            "photos": []
        }

    # ---------------------------------------------------------
    # SCORE EVERY PHOTO
    # ---------------------------------------------------------

    scored_results = []

    for result in all_results:

        title = result["title"]

        score = score_photo(
            title,
            place_name,
            location_name
        )

        scored_results.append({

            "title": title,

            "url": result["url"],

            "score": score
        })

    # ---------------------------------------------------------
    # SORT BEST MATCH FIRST
    # ---------------------------------------------------------

    scored_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # KEEP RELEVANT RESULTS
    # ---------------------------------------------------------

    relevant_results = [

        item

        for item in scored_results

        if item["score"] > 0
    ]

    # ---------------------------------------------------------
    # NO RELEVANT RESULTS
    # ---------------------------------------------------------

    if not relevant_results:

        print(
            f"[Wikimedia] Raw results existed, "
            f"but none were relevant for "
            f"'{place_name}'"
        )

        return {
            "success": False,

            "message": (
                f"No relevant Wikimedia photos "
                f"found for '{place_name}'."
            ),

            "photos": []
        }

    # ---------------------------------------------------------
    # SELECT TOP 10
    # ---------------------------------------------------------

    selected_results = relevant_results[:10]

    photos = [

        item["url"]

        for item in selected_results
    ]

    # ---------------------------------------------------------
    # DEBUG OUTPUT
    # ---------------------------------------------------------

    print(
        "\n[Wikimedia] Selected photos:"
    )

    for index, item in enumerate(
        selected_results,
        start=1
    ):

        print(
            f"{index}. "
            f"Score={item['score']} | "
            f"{item['title']}"
        )

    print(
        f"\n[Wikimedia] "
        f"{len(photos)} photos selected "
        f"for '{place_name}'"
    )

    # ---------------------------------------------------------
    # RETURN RESULT
    # ---------------------------------------------------------

    return {

        "success": True,

        "place_name":
            place_name,

        "location_name":
            location_name,

        "photos":
            photos
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    place = input(
        "Enter Attraction Name: "
    ).strip()

    location = input(
        "Enter Location/Country "
        "(optional): "
    ).strip()

    result = fetch_place_photos(
        place,
        location
    )

    print(
        "\n----------------------------"
    )

    if result["success"]:

        print(
            f"Photos found: "
            f"{len(result['photos'])}"
        )

        for i, photo in enumerate(
            result["photos"],
            start=1
        ):

            print(
                f"\nPhoto {i}:"
            )

            print(photo)

    else:

        print(
            result["message"]
        )