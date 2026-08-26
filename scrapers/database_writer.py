import sqlite3
import os

# Path to your SQLite database
DB_PATH = "data/travel_engine.db"


def save_place(
    name,
    latitude,
    longitude,
    history_summary,
    realness_status="Unknown"
):
    """
    Saves a place into the SQLite database.
    """

    # Check whether database exists
    if not os.path.exists(DB_PATH):
        return {
            "success": False,
            "message": "Database file not found."
        }

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT OR REPLACE INTO places
            (
                name,
                latitude,
                longitude,
                history_summary,
                realness_status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                latitude,
                longitude,
                history_summary,
                realness_status
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": f"{name} saved successfully."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        connection.close()


# -----------------------------
# Testing
# -----------------------------
if __name__ == "__main__":

    result = save_place(
        name="Goa",
        latitude=15.3004543,
        longitude=74.0855134,
        history_summary="Goa is a state on the southwestern coast of India.",
        realness_status="Underrated Gem"
    )

    print(result)