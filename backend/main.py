from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
from urllib.request import urlopen
from urllib.parse import quote

from scrapers.geocoder import get_coordinates
from scrapers.crawler import crawl_place
from scrapers.nearby_places import find_nearby_places


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="RouteMind Backend Engine"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

DB_PATH = "data/travel_engine.db"


# =========================================================
# REQUEST MODELS
# =========================================================

class SearchRequest(BaseModel):
    place: str


class SavePlaceRequest(BaseModel):
    place: str
    selected_index: int


# =========================================================
# ROUTE REQUEST MODELS
# =========================================================

class RouteLocation(BaseModel):
    name: str
    latitude: float
    longitude: float


class RouteRequest(BaseModel):
    locations: list[RouteLocation]


# =========================================================
# DATABASE HELPER
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def check_server_status():

    return {
        "status": "RouteMind Engine API Online",
        "infrastructure_cost": "$0"
    }


# =========================================================
# RETURN ALL SAVED PLACES
# =========================================================

@app.get("/api/places")
def stream_saved_places():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM places"
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# SEARCH PLACE / GEOCODING
# =========================================================

@app.post("/api/search")
def search_place(
    request: SearchRequest
):

    geo = get_coordinates(
        request.place
    )

    if not geo["success"]:
        return geo

    return {
        "success": True,
        "locations": geo["locations"]
    }


# =========================================================
# FIND NEARBY TOURIST PLACES
# =========================================================

@app.post("/api/nearby-places")
def nearby_places(
    request: SearchRequest
):

    result = find_nearby_places(
        request.place
    )

    return result


# =========================================================
# SAVE SELECTED PLACE
# =========================================================

@app.post("/api/save-place")
def save_selected_place(
    request: SavePlaceRequest
):

    result = crawl_place(
        request.place,
        request.selected_index
    )

    return result


# =========================================================
# ROUTE CALCULATION
# =========================================================
#
# This endpoint uses OSRM (Open Source Routing Machine)
# to calculate the actual road route between attractions.
#
# Input:
#
# {
#     "locations": [
#         {
#             "name": "Chapora Fort",
#             "latitude": 15.6136,
#             "longitude": 73.7395
#         },
#         {
#             "name": "Fort Aguada",
#             "latitude": 15.4922,
#             "longitude": 73.7737
#         }
#     ]
# }
#
# Output:
#
# {
#     "success": true,
#     "total_distance_km": ...,
#     "total_duration_minutes": ...,
#     "route": [...]
# }
#
# =========================================================

@app.post("/api/route")
def calculate_route(
    request: RouteRequest
):

    locations = request.locations

    # -----------------------------------------------------
    # CHECK NUMBER OF LOCATIONS
    # -----------------------------------------------------

    if len(locations) < 2:

        return {
            "success": False,
            "message": "At least 2 locations are required to calculate a route."
        }


    # -----------------------------------------------------
    # BUILD OSRM COORDINATE STRING
    # -----------------------------------------------------
    #
    # OSRM expects:
    #
    # longitude,latitude
    #
    # NOT:
    #
    # latitude,longitude
    #
    # -----------------------------------------------------

    coordinates = ";".join(
        f"{location.longitude},{location.latitude}"
        for location in locations
    )


    # -----------------------------------------------------
    # OSRM API URL
    # -----------------------------------------------------

    osrm_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        + quote(coordinates, safe=";,")
        + "?overview=full&geometries=geojson&steps=true"
    )


    # -----------------------------------------------------
    # CALL OSRM
    # -----------------------------------------------------

    try:

        with urlopen(
            osrm_url,
            timeout=30
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

    except Exception as error:

        return {
            "success": False,
            "message": "Unable to calculate route.",
            "error": str(error)
        }


    # -----------------------------------------------------
    # CHECK OSRM RESPONSE
    # -----------------------------------------------------

    if data.get("code") != "Ok":

        return {
            "success": False,
            "message": "Routing service could not find a route.",
            "routing_response": data
        }


    # -----------------------------------------------------
    # GET ROUTE
    # -----------------------------------------------------

    route = data["routes"][0]


    # -----------------------------------------------------
    # DISTANCE
    # -----------------------------------------------------
    #
    # OSRM returns distance in meters.
    #
    # Convert:
    #
    # meters -> kilometers
    #
    # -----------------------------------------------------

    total_distance_km = route["distance"] / 1000


    # -----------------------------------------------------
    # DURATION
    # -----------------------------------------------------
    #
    # OSRM returns duration in seconds.
    #
    # Convert:
    #
    # seconds -> minutes
    #
    # -----------------------------------------------------

    total_duration_minutes = route["duration"] / 60


    # -----------------------------------------------------
    # FORMAT STOP INFORMATION
    # -----------------------------------------------------

    stops = []

    for index, location in enumerate(locations):

        stops.append({
            "order": index + 1,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude
        })


    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {
        "success": True,

        "stops": stops,

        "total_distance_km": round(
            total_distance_km,
            2
        ),

        "total_duration_minutes": round(
            total_duration_minutes,
            1
        ),

        "total_duration_hours": round(
            total_duration_minutes / 60,
            2
        ),

        "route": route["geometry"]
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():

    return {
        "success": True,
        "message": "RouteMind Backend Running"
    }