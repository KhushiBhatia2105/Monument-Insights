
import os
import sqlite3
import numpy as np
from flask_cors import CORS
from tensorflow.keras.models import load_model
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPool2D, Flatten, Dense
import tensorflow as tf
import requests
from transformers import ViTForImageClassification, ViTImageProcessor
import torch
from PIL import Image
import io
import math

app = Flask(__name__)
app.secret_key = "your_secret_key"

CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------------- Database Setup ----------------------
DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------------------- User Class ----------------------
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], password=user[2])
    return None

# ---------------------- Routes ----------------------
@app.route("/")
def home():
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return jsonify({"message": "Signup successful!"}), 200
        except sqlite3.IntegrityError:
            return jsonify({"error": "Username already exists!"}), 400
        except Exception as e:
            return jsonify({"error": "An error occurred while saving the user."}), 500
        finally:
            conn.close()
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            user_obj = User(id=user[0], username=user[1], password=user[2])
            login_user(user_obj)
            return redirect(url_for("dashboard"))

        return "Invalid credentials!", 401
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/check_username", methods=["POST"])
def check_username():
    data = request.get_json()
    username = data.get("username")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    return jsonify({"exists": user is not None})

# ---------------------- Model Setup ----------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_1 = ViTForImageClassification.from_pretrained(
    "google/vit-base-patch16-224",
    num_labels=24,
    ignore_mismatched_sizes=True
)
model_1.load_state_dict(torch.load("vit_monument_model.pth", map_location=device))
model_1.to(device)
model_1.eval()

processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

class_names = { 
    'Ajanta Caves': (20.5519, 75.7033),
    'Charar-E- Sharif': (33.8776, 74.7739),
    'Chhota_Imambara': (26.8696, 80.9102),
    'Ellora Caves': (20.0268, 75.1768),
    'Fatehpur Sikri': (27.0937, 77.6600),
    'Gateway of India': (18.9220, 72.8347),
    'Humayuns Tomb': (28.5933, 77.2507),
    'India gate': (28.6129, 77.2295),
    'Khajuraho': (24.8318, 79.9199),
    'Sun Temple Konark': (19.8876, 86.0945),
    'alai_darwaza': (28.5245, 77.1855),
    'alai_minar': (28.5243, 77.1847),
    'basilica_of_bom_jesus': (15.5009, 73.9113),
    'charminar': (17.3616, 78.4747),
    'golden temple': (31.6200, 74.8765),
    'hawa mahal': (26.9239, 75.8267),
    'iron_pillar': (28.5244, 77.1856),
    'jamali_kamali_tomb': (28.5033, 77.1939),
    'lotus_temple': (28.5535, 77.2588),
    'mysore_palace': (12.3052, 76.6551),
    'qutub_minar': (28.5244, 77.1855),
    'tajmahal': (27.1751, 78.0421),
    'tanjavur temple': (10.7828, 79.1317),
    'victoria memorial': (22.5448, 88.3426)
}

def pred_and_plot(model, img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        pred_class_idx = torch.argmax(outputs.logits, dim=1).item()
        pred_class = list(class_names.keys())[pred_class_idx]
        coordinates = class_names[pred_class]

    return pred_class, coordinates

# ... (keep all the previous imports and setup code the same)

def get_nearby_places(lat, lng, radius=1000, limit=15):
    try:
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        (
          node["tourism"="hotel"](around:{radius},{lat},{lng});
          node["amenity"="restaurant"](around:{radius},{lat},{lng});
          node["amenity"="cafe"](around:{radius},{lat},{lng});
          node["tourism"="attraction"](around:{radius},{lat},{lng});
          node["historic"](around:{radius},{lat},{lng});
        );
        out center {limit};
        """
        
        response = requests.get(overpass_url, params={'data': overpass_query})
        response.raise_for_status()
        data = response.json()
        
        places = []
        for element in data.get('elements', []):
            if 'tags' in element and 'lat' in element and 'lon' in element:
                category = "hotel" if element.get('tags', {}).get('tourism') == "hotel" else \
                          "restaurant" if element.get('tags', {}).get('amenity') == "restaurant" else \
                          "cafe" if element.get('tags', {}).get('amenity') == "cafe" else \
                          "tourist_attraction"
                
                places.append({
                    "name": element['tags'].get('name', 'Unnamed Place'),
                    "location": [element['lat'], element['lon']],
                    "category": category
                })
        
        # Sort by distance to monument
        places.sort(key=lambda p: math.sqrt((p['location'][0]-lat)**2 + (p['location'][1]-lng)**2))
        
        return places[:15]
        
    except Exception as e:
        print(f"Error fetching nearby places: {e}")
        return []

# ... (keep all the remaining code the same)

@app.route("/monument/nearby", methods=["GET"])
@login_required
def get_nearby():
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    places = get_nearby_places(lat, lng)
    return jsonify(places)

@app.route("/monument", methods=["GET", "POST"])
@login_required
def monument():
    if request.method == "POST":
        file = request.files["file"]
        img = file.read()
        monument_type, coordinates = pred_and_plot(model_1, img)
        return jsonify({
            "monument_type": monument_type,
            "coordinates": coordinates
        })
    return render_template("monument.html")

if __name__ == "__main__":
    app.run(debug=True)