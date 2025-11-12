from flask import Flask, render_template, jsonify, request
import requests
import folium
import polyline
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# Initialize Firebase
cred = credentials.Certificate("ase-project-5abd5-firebase-adminsdk-fbsvc-5928608b4b.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# Replace with your actual Google Cloud API key
API_KEY = "AIzaSyABVUops1cgux3Oa2hBzdvfRR2KQokmCJk"


def geocode_address(address):
    """Convert a human-readable address to (lat, lng) using Google Geocoding API."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        return (location["lat"], location["lng"])
    else:
        raise RuntimeError(f"Geocoding failed: {data['status']}")


def get_route(origin, destination):
    """Fetch route data from Google Maps Routes API."""
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
    }
    data = {
        "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
        "destination": {"location": {"latLng": {"latitude": destination[0], "longitude": destination[1]}}},
        "travelMode": "DRIVE"
    }

    response = requests.post(url, headers=headers, json=data)

    print("=== GOOGLE ROUTES API RESPONSE ===")
    print("Status code:", response.status_code)
    print(response.text)
    print("==================================")

    if response.status_code == 200 and "routes" in response.json():
        return response.json()["routes"][0]
    else:
        raise RuntimeError(f"API Error {response.status_code}: {response.text}")



def plot_route(origin, destination, encoded_polyline):
    """Plot the route and save to HTML."""
    route_points = polyline.decode(encoded_polyline)
    midpoint = [(origin[0] + destination[0]) / 2, (origin[1] + destination[1]) / 2]

    m = folium.Map(location=midpoint, zoom_start=6)
    folium.PolyLine(route_points, color="blue", weight=4, opacity=0.8).add_to(m)
    folium.Marker(origin, tooltip="Origin", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(destination, tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)

    m.save("route_map.html")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_route", methods=["POST"])
def get_route_endpoint():
    data = request.get_json()
    origin_input = data["origin"]
    destination_input = data["destination"]

    def parse_input(value):
        try:
            lat, lng = map(float, value.split(","))
            return (lat, lng)
        except ValueError:
            return geocode_address(value)

    origin = parse_input(origin_input)
    destination = parse_input(destination_input)

    route = get_route(origin, destination)
    encoded_poly = route["polyline"]["encodedPolyline"]
    plot_route(origin, destination, encoded_poly)

    # Save to Firestore
    db.collection("routes").add({
        "origin": origin_input,
        "destination": destination_input,
        "distance_m": route["distanceMeters"],
        "duration": route["duration"],
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

    return jsonify({
        "distance_m": route["distanceMeters"],
        "duration": route["duration"],
        "map_url": "/route_map"
    })


@app.route("/route_map")
def show_map():
    with open("route_map.html", "r") as f:
        return f.read()


if __name__ == "__main__":
    app.run(debug=True)
