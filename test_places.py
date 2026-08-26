import os
import httpx

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY")


# --------------------------------------------------
# Categories we actually want for a travel app
# --------------------------------------------------
#
# FIX: "leisure.park" removed from the main request list.
# It was pulling in every park OSM knows about — Children's
# Park, Jogger's Park, "lions park" — regardless of whether
# it's actually a tourist attraction. If you want *notable*
# parks/gardens later, add them back with a stricter name
# check (see is_useful_place below) rather than the raw
# category.

CATEGORIES = [
    "tourism.sights",
    "tourism.attraction",
    "natural",
    "heritage",
    "building.historic",
    "entertainment.museum",
]


# --------------------------------------------------
# Things we DON'T want in our tourist list
# --------------------------------------------------
#
# FIX: added shop/market/generic-park words that were
# slipping through before.

EXCLUDED_WORDS = [
    "roadside cross",
    "cross",
    "statue",
    "assembly",
    "constituency",
    "railway",
    "station",
    "school",
    "college",
    "hospital",
    "police",
    "municipality",
    "municipal",
    "village",
    "ward",
    "election",
    "highway",
    "shop",
    "market",
    "store",
    "joggers",
    "jogger's",
    "children's park",
    "children park",
    "lions park",
    "playground",
    "parking",
    "toilet",
    "atm",
    "bank",
]



# --------------------------------------------------
# Category-based exclusions
# --------------------------------------------------
#
# FIX: name-based keyword filtering alone missed things like
# "Dr. B. R. Ambedkar" - the name has no bad keyword in it,
# but its category is tourism.attraction.artwork.statue.
# Small standalone statues/artworks are almost never the main
# reason someone visits a city, so we exclude by category
# regardless of what the place happens to be named.

EXCLUDED_CATEGORIES = [
    "artwork",
    "artwork.statue",
]


def is_useful_place(name, categories):
    """
    Decide whether a Geoapify result looks useful
    for RouteMind.
    """

    name_lower = name.lower()

    for word in EXCLUDED_WORDS:
        if word in name_lower:
            return False

    for category in categories:
        for excluded in EXCLUDED_CATEGORIES:
            if excluded in category:
                return False

    if name_lower in [
        "park",
        "garden",
        "cross",
        "monument",
        "viewpoint",
    ]:
        return False

    useful_category = False

    for category in categories:
        if (
            category.startswith("tourism")
            or category.startswith("natural")
            or category.startswith("heritage")
            or category.startswith("building.historic")
            or category.startswith("entertainment.museum")
        ):
            useful_category = True
            break

    return useful_category


def calculate_score(name, categories, popularity=None):
    """
    Give each place a simple RouteMind relevance score.
    Higher = more interesting as a tourist destination.

    FIX: now also folds in Geoapify's own "rank.popularity"
    value when the API provides it, so genuinely well-known
    places outrank obscure ones even if our keyword list
    doesn't happen to mention them by name.
    """

    name_lower = name.lower()

    score = 0

    strong_words = [
        "beach",
        "waterfall",
        "falls",
        "fort",
        "palace",
        "museum",
        "basilica",
        "cathedral",
        "church",
        "temple",
        "lake",
        "cave",
        "sanctuary",
        "viewpoint",
        "heritage",
        "island",
    ]

    for word in strong_words:
        if word in name_lower:
            score += 20

    for category in categories:
        if "beach" in category:
            score += 25
        elif "waterfall" in category:
            score += 25
        elif "castle" in category:
            score += 25
        elif "museum" in category:
            score += 20
        elif "viewpoint" in category:
            score += 15
        elif "archaeological" in category:
            score += 15
        elif "attraction" in category:
            score += 10

    # FIX: popularity bonus, scaled 0-30. Geoapify's
    # rank.popularity is typically a small float (e.g. 0-10),
    # so we scale it up rather than adding it raw.
    if popularity:
        score += min(popularity * 3, 30)

    return score


def geocode_place(place_name):
    """
    FIX / NEW: Geocodes a place name and returns not just
    coordinates, but the Geoapify "place_id" for it when the
    result is an administrative area (state, district, city).

    That place_id is the key to fixing the coverage problem -
    it lets Places API search the place's REAL boundary polygon
    instead of a fixed-radius circle from a single point.
    """

    url = "https://api.geoapify.com/v1/geocode/search"

    params = {
        "text": place_name,
        "format": "json",
        "apiKey": API_KEY,
    }

    response = httpx.get(url, params=params, timeout=20)

    if response.status_code != 200:
        print("Geocoding HTTP Error:", response.status_code)
        print(response.text)
        return None

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    top = results[0]

    return {
        "latitude": top.get("lat"),
        "longitude": top.get("lon"),
        "place_id": top.get("place_id"),
        "formatted": top.get("formatted"),
        "result_type": top.get("result_type"),  # e.g. "state", "city"
    }


def find_tourist_places(latitude=None, longitude=None, place_id=None, radius=30000, limit=100):
    """
    FIX: now supports two modes.

    1. place_id given (preferred, used for states/regions/
       cities): searches the ACTUAL boundary polygon of that
       place via filter=place:{place_id}. This is what makes
       Baga Beach, Calangute, Anjuna, Vagator, and Dudhsagar
       Falls show up for a "Goa" search - they're all inside
       the state boundary but were outside a 30km circle from
       the state's center point.

    2. Only latitude/longitude given (no place_id): falls back
       to the old circle search - still useful for "places near
       me" style queries where you genuinely want a radius, not
       an entire state.

    limit raised from 50 to 100 by default since a whole-state
    boundary search returns far more candidates than a small
    circle did - filtering happens after, so more raw candidates
    means a better final shortlist, not more noise shown to users.
    """

    url = "https://api.geoapify.com/v2/places"

    params = {
        "categories": ",".join(CATEGORIES),
        "limit": limit,
        "apiKey": API_KEY,
    }

    if place_id:
        params["filter"] = f"place:{place_id}"
    elif latitude is not None and longitude is not None:
        params["filter"] = f"circle:{longitude},{latitude},{radius}"
    else:
        raise ValueError("Provide either place_id, or both latitude and longitude.")

    response = httpx.get(url, params=params, timeout=30)

    if response.status_code != 200:
        print("HTTP Error:", response.status_code)
        print(response.text)
        return []

    data = response.json()

    return data.get("features", [])


def check_wikidata(place_id):
    """
    FIX / NEW: Confirms a place is "real world notable" by
    checking whether Geoapify's Place Details endpoint finds
    a linked Wikidata entry for it. Genuine attractions (forts,
    waterfalls, heritage buildings) almost always have one.
    Random benches, statues, and shops almost never do.

    Call this only on your already-filtered shortlist (e.g. top
    15-20 by score) - it's one extra HTTP call per place, so you
    don't want to run it on all 50 raw results.

    Returns the wikidata ID string, or None if not found.
    """

    if not place_id:
        return None

    url = "https://api.geoapify.com/v2/place-details"

    params = {
        "id": place_id,
        "features": "details",
        "apiKey": API_KEY,
    }

    try:
        response = httpx.get(url, params=params, timeout=15)
    except httpx.RequestError:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    features = data.get("features", [])

    if not features:
        return None

    properties = features[0].get("properties", {})
    wiki = properties.get("wiki_and_media", {})

    return wiki.get("wikidata")


def get_clean_tourist_places(place_name=None, latitude=None, longitude=None, verify_with_wikidata=True, top_n=15):
    """
    Full pipeline: geocode -> raw Geoapify results -> filtered ->
    scored -> sorted -> (optionally) Wikidata-verified top N.

    This is the function your FastAPI router should import
    and call.

    FIX: now takes place_name (preferred) and geocodes it
    internally, using the boundary-search fix above. This is
    the call your /search endpoint should actually make - pass
    what the user typed ("Goa"), not raw coordinates, so the
    whole-state boundary search kicks in automatically.

    latitude/longitude are still accepted directly for the
    "search near my current GPS location" case, where a circle
    radius is genuinely what you want instead of a state
    boundary.
    """

    if place_name:
        geocoded = geocode_place(place_name)

        if not geocoded:
            return []

        raw_places = find_tourist_places(
            place_id=geocoded["place_id"],
            latitude=geocoded["latitude"],
            longitude=geocoded["longitude"],
        )

    elif latitude is not None and longitude is not None:
        raw_places = find_tourist_places(latitude=latitude, longitude=longitude, radius=30000)

    else:
        raise ValueError("Provide either place_name, or both latitude and longitude.")

    clean_places = []
    seen_names = set()

    for feature in raw_places:
        properties = feature.get("properties", {})

        name = properties.get("name")
        categories = properties.get("categories", [])
        lat = properties.get("lat")
        lon = properties.get("lon")
        place_id = properties.get("place_id")
        popularity = properties.get("rank", {}).get("popularity")

        if not name:
            continue

        if not is_useful_place(name, categories):
            continue

        name_key = name.lower().strip()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        score = calculate_score(name, categories, popularity)

        clean_places.append({
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "categories": categories,
            "place_id": place_id,
            "score": score,
            "wikidata": None,
        })

    clean_places.sort(key=lambda p: p["score"], reverse=True)

    shortlist = clean_places[:top_n]

    if verify_with_wikidata:
        verified = []
        for place in shortlist:
            wikidata_id = check_wikidata(place["place_id"])
            place["wikidata"] = wikidata_id
            # Keep it even without wikidata for now - treat
            # wikidata as a score boost/trust signal, not a
            # hard filter, since some real attractions (esp.
            # in smaller towns) genuinely lack a Wikidata entry.
            if wikidata_id:
                place["score"] += 15
            verified.append(place)

        verified.sort(key=lambda p: p["score"], reverse=True)
        return verified

    return shortlist


# ==================================================
# TEST (run directly: python services/places.py)
# ==================================================

if __name__ == "__main__":

    place = input("Enter Place Name: ")

    # FIX: no longer hardcoded to Goa's coordinates - any
    # place name now works, since geocode_place() + the
    # boundary search handle it.
    results = get_clean_tourist_places(place_name=place)

    print("\n----------------------------")

    if not results:
        print("No useful tourist places found.")
    else:
        print(f"Found {len(results)} useful tourist places:\n")

        for index, place in enumerate(results, start=1):
            print(f"{index}. {place['name']}")
            print(f"   Score: {place['score']}")
            print(f"   Wikidata: {place['wikidata']}")
            print(f"   Latitude: {place['latitude']}")
            print(f"   Longitude: {place['longitude']}")
            print(f"   Category: {place['categories']}")
            print()