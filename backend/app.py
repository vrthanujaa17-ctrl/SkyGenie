from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
import json
import os
import time
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

CACHE_FILE = "last_successful_flights.json"

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
    {
        "airline": "American Airlines",
        "origin": "JFK",
        "destination": "LAX",
        "departureTime": "2026-06-15T09:30:00",
        "arrivalTime": "2026-06-15T14:15:00",
        "price": "USD 245.75",
        "currency": "USD",
        "durationMinutes": 345,
        "stopCount": 1,
        "layoverMinutes": 55,
    },
]


def save_cached_flights(cache_payload):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Could not save cache: {e}")


def load_cached_flights():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Could not load cache: {e}")
    return None


def safe_get(data, *keys, default=None):
    current = data
    for key in keys:
        try:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and isinstance(key, int):
                current = current[key]
            else:
                return default
        except Exception:
            return default

        if current is None:
            return default
    return current


def normalize_airport_code(value):
    if isinstance(value, dict):
        return (
            value.get("displayCode")
            or value.get("skyId")
            or value.get("id")
            or value.get("name")
            or "N/A"
        )
    return str(value) if value else "N/A"


def parse_itinerary(item):
    if not isinstance(item, dict):
        return None

    leg = None
    legs = item.get("legs", [])
    if isinstance(legs, list) and legs:
        leg = legs[0]
    elif isinstance(item.get("leg"), dict):
        leg = item.get("leg")

    if not leg:
        return None

    carriers = safe_get(leg, "carriers", "marketing", default=[])
    airline = "Unknown"
    if isinstance(carriers, list) and carriers:
        first_carrier = carriers[0]
        if isinstance(first_carrier, dict):
            airline = first_carrier.get("name", "Unknown")

    price = (
        safe_get(item, "price", "formatted", default=None)
        or safe_get(item, "price", "displayAmount", default=None)
        or safe_get(item, "formattedPrice", default=None)
        or "N/A"
    )

    currency = (
        safe_get(item, "price", "currency", default=None)
        or safe_get(item, "currency", default=None)
        or "USD"
    )

    origin = normalize_airport_code(leg.get("origin"))
    destination = normalize_airport_code(leg.get("destination"))

    departure_time = (
        leg.get("departure")
        or leg.get("departureTime")
        or leg.get("depart")
        or "N/A"
    )

    arrival_time = (
        leg.get("arrival")
        or leg.get("arrivalTime")
        or "N/A"
    )

    duration = (
        leg.get("durationInMinutes")
        or leg.get("durationMinutes")
        or leg.get("duration")
        or 0
    )

    stop_count = leg.get("stopCount")
    if stop_count is None:
        segments = leg.get("segments", [])
        if isinstance(segments, list) and len(segments) > 0:
            stop_count = max(len(segments) - 1, 0)
        else:
            stop_count = 0

    layover_minutes = 0
    segments = leg.get("segments", [])
    if isinstance(segments, list) and len(segments) > 1:
        total_segment_minutes = 0
        for segment in segments:
            seg_duration = (
                segment.get("durationInMinutes")
                or segment.get("durationMinutes")
                or 0
            )
            if isinstance(seg_duration, (int, float)):
                total_segment_minutes += seg_duration

        if isinstance(duration, (int, float)):
            layover_minutes = max(duration - total_segment_minutes, 0)

    return {
        "airline": airline,
        "origin": origin,
        "destination": destination,
        "departureTime": departure_time,
        "arrivalTime": arrival_time,
        "price": price,
        "currency": currency,
        "durationMinutes": duration if isinstance(duration, (int, float)) else 0,
        "stopCount": stop_count if isinstance(stop_count, int) else 0,
        "layoverMinutes": layover_minutes,
    }


def extract_itineraries(data):
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            if "legs" in obj and isinstance(obj.get("legs"), list):
                found.append(obj)

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)

    unique = []
    seen = set()

    for item in found:
        marker = str(item)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)

    return unique


def call_api_with_retries(url, headers, params, attempts=1, timeout=60):
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            print(f"Attempt {attempt}/{attempts}")
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            print("STATUS CODE:", response.status_code)
            print("RAW RESPONSE:", response.text[:4000])
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"Timeout on attempt {attempt}: {e}")
            if attempt < attempts:
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"Request failed on attempt {attempt}: {e}")
            if attempt < attempts:
                time.sleep(2)

    raise last_error


def is_provider_blocked(error_text):
    text = (error_text or "").lower()
    return (
        "reason\":\"blocked" in text
        or "captcha" in text
        or "403 forbidden" in text
        or "redirect_to" in text
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    query = data.get("query", "").strip()
    print(f"Received query from chat window: {query}")

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
        print(f"CRITICAL CHAT ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "status": "Backend is running",
            "endpoints": [
                "/health",
                "/flights?from=NYC&to=LAX&date=2026-06-15",
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
            "cached_flights_available": bool(load_cached_flights()),
        }
    )


@app.route("/api/landmarks", methods=["GET"])
def get_landmarks():
    landmarks = [
        {
            "id": 1,
            "name": "Eiffel Tower",
            "location": "Paris, France",
            "description": "A wrought-iron lattice tower on the Champ de Mars.",
            "image_url": "http://127.0.0.1:5001/static/images/eiffel.png",
        },
        {
            "id": 2,
            "name": "Colosseum",
            "location": "Rome, Italy",
            "description": "An oval amphitheatre in the centre of the city.",
            "image_url": "http://127.0.0.1:5001/static/images/colosseum.png",
        },
    ]
    return jsonify(landmarks)


@app.route("/flights", methods=["GET"])
def get_flights():
    source = request.args.get("from", "").strip().upper()
    destination = request.args.get("to", "").strip().upper()
    date = request.args.get("date", "").strip()

    city_to_airport = {
        "NYC": "JFK",
        "NEW YORK": "JFK",
        "LAX": "LAX",
        "LOS ANGELES": "LAX",
        "CHI": "ORD",
        "CHICAGO": "ORD",
        "SFO": "SFO",
        "SAN FRANCISCO": "SFO",
    }

    source = city_to_airport.get(source, source)
    destination = city_to_airport.get(destination, destination)

    if not source or not destination or not date:
        return jsonify(
            {
                "error": "Missing required query parameters: from, to, date",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
                "message": "Missing search parameters. Showing demo flight data.",
            }
        ), 400

    if not SKYSCANNER_API_KEY:
        return jsonify(
            {
                "message": "Flight API key missing in .env. Showing demo flight data.",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
            }
        ), 200

    url = f"https://{SKYSCANNER_API_HOST}/web/flights/search-one-way"

    querystring = {
        "placeIdFrom": source,
        "placeIdTo": destination,
        "departDate": date,
        "adults": "1",
        "cabinClass": "economy",
        "currency": "USD",
        "market": "US",
        "locale": "en-US",
    }

    headers = {
        "x-rapidapi-key": SKYSCANNER_API_KEY,
        "x-rapidapi-host": SKYSCANNER_API_HOST,
    }

    try:
        print("API HOST:", SKYSCANNER_API_HOST)
        print("REQUEST URL:", url)
        print("QUERYSTRING:", querystring)

        response = call_api_with_retries(
            url=url,
            headers=headers,
            params=querystring,
            attempts=1,
            timeout=60,
        )

        data = response.json()
        itineraries = extract_itineraries(data)

        flights = []
        for item in itineraries:
            parsed = parse_itinerary(item)
            if parsed:
                flights.append(parsed)

        if not flights:
            return jsonify(
                {
                    "message": "Live API responded, but no parsable flights were found. Showing demo flight data.",
                    "fallback_used": True,
                    "cached_used": False,
                    "fallback": MOCK_FLIGHTS,
                    "raw_itinerary_count": len(itineraries),
                    "debug_preview": data,
                }
            ), 200

        cache_payload = {
            "message": "Live flight results fetched successfully.",
            "fallback_used": False,
            "cached_used": False,
            "flights": flights,
            "source": source,
            "destination": destination,
            "date": date,
        }
        save_cached_flights(cache_payload)

        return jsonify(cache_payload), 200

    except requests.exceptions.Timeout as e:
        print("FINAL TIMEOUT ERROR:", e)
        cached = load_cached_flights()
        if cached:
            return jsonify(
                {
                    "message": "Live flight search timed out, so the last saved results are being shown.",
                    "fallback_used": False,
                    "cached_used": True,
                    "flights": cached.get("flights", MOCK_FLIGHTS),
                    "error": str(e),
                }
            ), 200

        return jsonify(
            {
                "message": "Live flight search timed out, so demo flight data is being shown.",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
                "error": str(e),
            }
        ), 200

    except requests.exceptions.HTTPError as e:
        print("HTTP ERROR:", e)
        error_text = str(e)
        cached = load_cached_flights()

        if cached:
            if is_provider_blocked(error_text):
                return jsonify(
                    {
                        "message": "The flight provider temporarily blocked live access, so the last saved results are being shown.",
                        "fallback_used": False,
                        "cached_used": True,
                        "flights": cached.get("flights", MOCK_FLIGHTS),
                        "error": error_text,
                    }
                ), 200

            return jsonify(
                {
                    "message": "Live flight data is temporarily unavailable, so the last saved results are being shown.",
                    "fallback_used": False,
                    "cached_used": True,
                    "flights": cached.get("flights", MOCK_FLIGHTS),
                    "error": error_text,
                }
            ), 200

        if is_provider_blocked(error_text):
            return jsonify(
                {
                    "message": "The flight provider temporarily blocked live access, so demo flight data is being shown.",
                    "fallback_used": True,
                    "cached_used": False,
                    "fallback": MOCK_FLIGHTS,
                    "error": error_text,
                }
            ), 200

        return jsonify(
            {
                "message": "Live flight data is temporarily unavailable, so demo flight data is being shown.",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
                "error": error_text,
            }
        ), 200

    except requests.exceptions.RequestException as e:
        print("REQUEST ERROR:", e)
        cached = load_cached_flights()
        if cached:
            return jsonify(
                {
                    "message": "Network/API request failed, so the last saved results are being shown.",
                    "fallback_used": False,
                    "cached_used": True,
                    "flights": cached.get("flights", MOCK_FLIGHTS),
                    "error": str(e),
                }
            ), 200

        return jsonify(
            {
                "message": "Network/API request failed, so demo flight data is being shown.",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
                "error": str(e),
            }
        ), 200

    except Exception as e:
        print("UNEXPECTED ERROR:", e)
        cached = load_cached_flights()
        if cached:
            return jsonify(
                {
                    "message": "An unexpected issue occurred, so the last saved results are being shown.",
                    "fallback_used": False,
                    "cached_used": True,
                    "flights": cached.get("flights", MOCK_FLIGHTS),
                    "error": str(e),
                }
            ), 200

        return jsonify(
            {
                "message": "An unexpected issue occurred, so demo flight data is being shown.",
                "fallback_used": True,
                "cached_used": False,
                "fallback": MOCK_FLIGHTS,
                "error": str(e),
            }
        ), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)