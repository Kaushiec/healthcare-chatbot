from backend.database import get_connection


def fetch_rows(query: str, params: tuple = ()) -> list[dict]:
    connection = None
    cursor = None

    try:
        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, params)

        results = cursor.fetchall()

        return results

    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            if connection is not None:
                connection.close()