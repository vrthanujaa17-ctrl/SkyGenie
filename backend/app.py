from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
import os
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SKYSCANNER_API_KEY = os.getenv("SKYSCANNER_API_KEY", "").strip()
SKYSCANNER_API_HOST = os.getenv(
    "SKYSCANNER_API_HOST", "flights-sky.p.rapidapi.com"
).strip()

MOCK_FLIGHTS = [
    {
        "airline": "United",
        "origin": "EWR",
        "destination": "LAX",
        "departureTime": "2026-06-15T07:00:00",
        "arrivalTime": "2026-06-15T09:56:00",
        "price": "USD 164.52",
        "currency": "USD",
        "durationMinutes": 356,
        "stopCount": 0,
        "layoverMinutes": 0,
    },
    {
        "airline": "Delta",
        "origin": "JFK",
        "destination": "LAX",
        "departureTime": "2026-06-15T08:00:00",
        "arrivalTime": "2026-06-15T11:15:00",
        "price": "USD 220.00",
        "currency": "USD",
        "durationMinutes": 315,
        "stopCount": 0,
        "layoverMinutes": 0,
    },
]


def normalize_entity(value: str) -> str:
    """
    Map user-facing city/airport codes to entity IDs expected by the round-trip API.
    Update this mapping as you find valid entity IDs.
    """
    city_to_entity = {
        "PARIS": "PARI",
        "PARI": "PARI",
        "LONDON": "LOND",
        "LOND": "LOND",

        # These are placeholders until you confirm the actual entity IDs.
        # If you know the exact entity IDs from the API docs or search endpoint,
        # replace them here.
        "NYC": "NYCA",
        "NEW YORK": "NYCA",
        "LAX": "LAXA",
        "LOS ANGELES": "LAXA",
        "SFO": "SFOA",
        "SAN FRANCISCO": "SFOA",
        "CHICAGO": "CHIA",
        "CHI": "CHIA",
    }
    return city_to_entity.get(value.upper(), value.upper())


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"answer": "Please enter a travel-related question."}), 400

    if not GEMINI_API_KEY or client is None:
        return jsonify(
            {
                "answer": "The chatbot is not configured yet. Please add GEMINI_API_KEY to your .env file."
            }
        ), 500

    try:
        prompt = f"""
You are a helpful travel assistant chatbot.

Answer like a clean, normal travel chatbot.

Formatting rules:
- Do NOT use markdown symbols like **, ##, *, or backticks.
- Use simple plain text only.
- Keep the answer organized with short sections.
- If giving an itinerary, format it like:
Day 1:
- place/activity
- place/activity

Day 2:
- place/activity
- place/activity

Then add short sections like:
Food Tips:
Transport:
Budget Tips:

Keep the answer practical, friendly, and easy to read.
Do not mention any uploaded document or sample document.
Do not invent live flight prices, real-time schedules, visa rules, or current legal/policy information. For those, say live verification may be needed.

User question:
{query}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[prompt],
        )
        answer_text = getattr(response, "text", None) or "Sorry, I could not generate a response."
        return jsonify({"answer": answer_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "status": "Backend is running",
            "endpoints": [
                "/health",
                "/flights?from=PARIS&to=LONDON&date=2026-06-15&returnDate=2026-06-22",
                "/chat",
            ],
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "gemini_api_configured": bool(GEMINI_API_KEY),
            "skyscanner_api_configured": bool(SKYSCANNER_API_KEY),
            "api_host": SKYSCANNER_API_HOST,
        }
    )


@app.route("/flights", methods=["GET"])
def get_flights():
    source = request.args.get("from", "").strip().upper()
    destination = request.args.get("to", "").strip().upper()
    depart_date = request.args.get("date", "").strip()
    return_date = request.args.get("returnDate", "").strip()

    if not source or not destination or not depart_date or not return_date:
        return jsonify(
            {
                "error": "Missing required query parameters: from, to, date, returnDate",
                "fallback_used": True,
                "outbound_flights": MOCK_FLIGHTS,
                "return_flights": MOCK_FLIGHTS,
                "message": "Missing search parameters. Showing demo data.",
            }
        ), 400

    if not SKYSCANNER_API_KEY:
        return jsonify(
            {
                "message": "Flight API key missing in .env. Showing demo data.",
                "fallback_used": True,
                "outbound_flights": MOCK_FLIGHTS,
                "return_flights": MOCK_FLIGHTS,
            }
        ), 200

    from_entity = normalize_entity(source)
    to_entity = normalize_entity(destination)

    url = f"https://{SKYSCANNER_API_HOST}/flights/search-roundtrip"

    querystring = {
        "fromEntityId": from_entity,
        "toEntityId": to_entity,
        "departDate": depart_date,
        "returnDate": return_date,
    }

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": SKYSCANNER_API_KEY,
        "x-rapidapi-host": SKYSCANNER_API_HOST,
    }

    try:
        print("ROUNDTRIP URL:", url)
        print("ROUNDTRIP QUERYSTRING:", querystring)

        response = requests.get(url, headers=headers, params=querystring, timeout=60)

        print("STATUS CODE:", response.status_code)
        print("RAW RESPONSE:", response.text[:5000])

        response.raise_for_status()

        data_json = response.json()

        # Handle API-level errors returned inside a 200 response
        if not data_json.get("data"):
            return jsonify(
                {
                    "message": data_json.get("message", "API returned no usable data."),
                    "fallback_used": True,
                    "outbound_flights": MOCK_FLIGHTS,
                    "return_flights": MOCK_FLIGHTS,
                    "api_errors": data_json.get("errors", {}),
                }
            ), 200

        itineraries = data_json.get("data", {}).get("itineraries", [])

        outbound_flights = []
        return_flights = []

        for item in itineraries:
            try:
                price = item.get("price", {}).get("formatted", "N/A")
                legs = item.get("legs", [])

                # Outbound
                if len(legs) > 0:
                    leg = legs[0]
                    outbound_flights.append(
                        {
                            "airline": leg.get("carriers", {})
                            .get("marketing", [{}])[0]
                            .get("name", "Unknown"),
                            "origin": leg.get("origin", {}).get("displayCode", ""),
                            "destination": leg.get("destination", {}).get("displayCode", ""),
                            "departureTime": leg.get("departure", ""),
                            "arrivalTime": leg.get("arrival", ""),
                            "price": price,
                            "currency": "USD",
                            "stopCount": leg.get("stopCount", 0),
                            "durationMinutes": leg.get("durationInMinutes", 0),
                            "layoverMinutes": 0,
                        }
                    )

                # Return
                if len(legs) > 1:
                    leg = legs[1]
                    return_flights.append(
                        {
                            "airline": leg.get("carriers", {})
                            .get("marketing", [{}])[0]
                            .get("name", "Unknown"),
                            "origin": leg.get("origin", {}).get("displayCode", ""),
                            "destination": leg.get("destination", {}).get("displayCode", ""),
                            "departureTime": leg.get("departure", ""),
                            "arrivalTime": leg.get("arrival", ""),
                            "price": price,
                            "currency": "USD",
                            "stopCount": leg.get("stopCount", 0),
                            "durationMinutes": leg.get("durationInMinutes", 0),
                            "layoverMinutes": 0,
                        }
                    )

            except Exception as e:
                print("Parsing error:", e)

        return jsonify(
            {
                "message": "Round-trip flights parsed successfully.",
                "fallback_used": False,
                "outbound_flights": outbound_flights,
                "return_flights": return_flights,
            }
        ), 200

    except requests.exceptions.RequestException as e:
        return jsonify(
            {
                "message": "Round-trip API call failed. Showing demo data.",
                "error": str(e),
                "fallback_used": True,
                "outbound_flights": MOCK_FLIGHTS,
                "return_flights": MOCK_FLIGHTS,
            }
        ), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)