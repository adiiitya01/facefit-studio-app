from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
import mysql.connector
import bcrypt
import secrets
import dlib
import cv2
import numpy as np
import os
import logging

# Initialize the app
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Directory for uploaded images
Session(app)
CORS(app, origins=['http://127.0.0.1:5500'], supports_credentials=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# CORS setup
CORS(app, resources={
    r"/signup": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/login": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/check_session": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/logout": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/detect_face_shape": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    },
    r"/get_username": {
        "origins": "http://127.0.0.1:5500",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:5500'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    print("CORS Headers added:", response.headers)
    return response

# Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="@aditya3084",
            database="face_shape_app"
        )
        print("Database connection successful")
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

# Signup endpoint
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    # Placeholder: Add user to database (e.g., SQLite, PostgreSQL)
    # For now, return a mock response
    if username and password:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 400

# Login endpoint
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        print("Received OPTIONS request for /login")
        return '', 200
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        print("Missing username or password")
        return jsonify({'error': 'Username and password are required'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0]
            print(f"Retrieved password: {stored_password}")
            print(f"Password type: {type(stored_password)}, Length: {len(stored_password)}")
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
                print(f"Encoded password: {stored_password}")
            elif not isinstance(stored_password, bytes):
                print(f"Invalid password format: {stored_password}")
                return jsonify({'error': 'Invalid password format in database'}), 500
            if not stored_password.startswith(b'$2b$'):
                print(f"Invalid bcrypt hash format: {stored_password}")
                return jsonify({'error': 'Invalid bcrypt hash format in database'}), 500
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['username'] = username
                print(f"Login successful for {username}, redirecting to index.html")
                return jsonify({'message': 'Login successful', 'redirect': 'http://127.0.0.1:5500/'}), 200
            else:
                print("Invalid credentials")
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            print(f"User not found: {username}")
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/get_username', methods=['GET', 'OPTIONS'])
def get_username():
    if request.method == 'OPTIONS':
        print("Received OPTIONS request for /get_username")
        return '', 200
    if 'username' in session:
        print(f"Returning username: {session['username']}")
        return jsonify({'username': session['username']}), 200
    else:
        print("No user logged in")
        return jsonify({'error': 'Not logged in'}), 401

# Session check endpoint
@app.route('/check_session', methods=['GET'])
def check_session():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

# Logout endpoint
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully', 'redirect': 'login.html'})

# Face shape detection endpoint
@app.route('/detect_face_shape', methods=['POST', 'OPTIONS'])
def detect_face_shape():
    if request.method == 'OPTIONS':
        print("Received OPTIONS request for /detect_face_shape")
        return '', 200
    if 'username' not in session:
        print("User not logged in")
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'image' not in request.files:
        print("No image in request.files")
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    
    print(f"Received file: {file.filename}, Size: {file.content_length}")

    try:
        file_content = file.read()
        print(f"File content length: {len(file_content)} bytes")
        if not file_content:
            print("Empty file content")
            return jsonify({'error': 'Empty image file'}), 400

        img_array = np.frombuffer(file_content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            print("Failed to decode image. File content:", file_content[:100] if file_content else "None")
            return jsonify({'error': 'Failed to process image'}), 400

        print(f"Image decoded: Shape {img.shape}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        predictor_path = "C:\\Users\\ADITYA\\Desktop\\face_shape_app\\shape_predictor_68_face_landmarks.dat"
        if not os.path.exists(predictor_path):
            print("Shape predictor file not found at specified path")
            return jsonify({'error': 'Shape predictor file not found'}), 500

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(predictor_path)

        faces = detector(gray)
        print(f"Detected {len(faces)} faces")
        if len(faces) == 0:
            return jsonify({'error': 'No face detected'}), 400

        shape = predictor(gray, faces[0])
        landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

        jaw_points = landmarks[0:17]
        forehead_points = landmarks[17:27]
        face_length = abs(landmarks[8][1] - landmarks[27][1])  # Chin to forehead
        jaw_width = abs(jaw_points[0][0] - jaw_points[16][0])  # Width of jaw
        forehead_width = abs(forehead_points[0][0] - forehead_points[9][0])  # Width of forehead
        cheekbone_width = abs(landmarks[1][0] - landmarks[15][0])  # Width of cheekbones

        # Debugging: Print measurements to understand the values
        print(f"Measurements - Face Length: {face_length}, Jaw Width: {jaw_width}, Forehead Width: {forehead_width}, Cheekbone Width: {cheekbone_width}")

        # Ratios for face shape determination
        length_to_jaw_ratio = face_length / jaw_width if jaw_width != 0 else 0
        length_to_forehead_ratio = face_length / forehead_width if forehead_width != 0 else 0
        jaw_to_forehead_diff = abs(jaw_width - forehead_width)
        jaw_to_cheekbone_diff = abs(jaw_width - cheekbone_width)

        # Debug ratios
        print(f"Ratios - Length/Jaw: {length_to_jaw_ratio}, Length/Forehead: {length_to_forehead_ratio}, Jaw-Forehead Diff: {jaw_to_forehead_diff}, Jaw-Cheekbone Diff: {jaw_to_cheekbone_diff}")

        # Improved face shape detection logic
        if length_to_jaw_ratio > 1.5 and jaw_to_forehead_diff < 10:
            face_shape = "Oval"  # Face is longer than wide, jaw and forehead nearly equal
        elif length_to_jaw_ratio > 2.0:
            face_shape = "Oblong"  # Face is much longer than wide
        elif length_to_jaw_ratio < 1.2 and jaw_to_forehead_diff < 10:
            face_shape = "Square"  # Jaw and forehead nearly equal, face not elongated
        elif length_to_jaw_ratio < 1.2 and jaw_width > forehead_width and jaw_width > cheekbone_width:
            face_shape = "Triangle"  # Wider jaw, narrower forehead and cheekbones
        elif cheekbone_width > jaw_width and cheekbone_width > forehead_width and length_to_jaw_ratio < 1.5:
            face_shape = "Diamond"  # Widest at cheekbones, narrower jaw and forehead
        elif forehead_width > jaw_width and cheekbone_width > jaw_width and length_to_jaw_ratio < 1.5:
            face_shape = "Heart"  # Wider forehead and cheekbones, narrower jaw
        else:
            face_shape = "Round"  # Default case: face is nearly as wide as it is long

        print(f"Face shape detected: {face_shape}")

        # Map detected shape to the corresponding HTML page
        face_shape_pages = {
            'Oval': 'http://127.0.0.1:5500/oval.html',
            'Round': 'http://127.0.0.1:5500/round.html',
            'Square': 'http://127.0.0.1:5500/square.html',
            'Heart': 'http://127.0.0.1:5500/heart.html',
            'Diamond': 'http://127.0.0.1:5500/diamond.html',
            'Oblong': 'http://127.0.0.1:5500/oblong.html',
            'Triangle': 'http://127.0.0.1:5500/triangle.html'
        }

        redirect_url = face_shape_pages.get(face_shape, 'http://127.0.0.1:5500/index.html')
        print(f"Redirecting to {redirect_url} for face shape {face_shape}")
        return jsonify({'message': f'Face shape detected: {face_shape}', 'redirect': redirect_url}), 200

    except Exception as e:
        print(f"Error in detect_face_shape: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)