from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import csv
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time, tempfile, threading
from datetime import datetime
from geopy.distance import geodesic
import sounddevice as sd
from scipy.io.wavfile import write
import random
import base64
from models.ai_model import ai_model
import smtplib
from email.mime.text import MIMEText
from playsound import playsound
app = Flask(__name__)
app.secret_key = 'NombongoGxekiwe'
from flask_mail import Mail, Message
import sys
sys.stdout.reconfigure(line_buffering=True)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gxekiwebongeka@gmail.com'        # Replace
app.config['MAIL_PASSWORD'] = 'lvelgsxpyneuyllh'           # Use app password
app.config['MAIL_DEFAULT_SENDER'] = ('DangerAlert System', 'gxekiwebongeka@gmail.com')

mail = Mail(app)
# Ensure CSV file exists
def init_csv():
    if not os.path.exists('users.csv'):
        with open('users.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['FirstName', 'LastName', 'IdNumber', 'Cellphone', 'Email', 'Username', 'Consent'])
@app.route('/')
def landing_page():
    return render_template('index.html')  # Make sure your HTML file is located in the 'templates' folder
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        id_number = request.form['id_number']
        cellphone = request.form['cellphone']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        consent = request.form.get('consent')

        if not (firstname and lastname and id_number and cellphone and email and username and password and confirm_password and consent):
            return render_template('register.html', error='All fields are required!')

        if len(id_number) != 13 or not id_number.isdigit():
            return render_template('register.html', error='ID Number must be 13 digits!')

        if len(cellphone) != 10 or not cellphone.isdigit():
            return render_template('register.html', error='Cellphone number must be 10 digits!')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match!')

        hashed_password = generate_password_hash(password)

        with open('users.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([firstname, lastname, id_number, cellphone, email, username, hashed_password])

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            return render_template('login.html', error='Please fill in both fields.')

        try:
            with open('users.csv', mode='r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 7 and row[5] == username:
                        if check_password_hash(row[6], password):
                            session['username'] = username
                            return redirect(url_for('dashboard'))
                        else:
                            return render_template('login.html', error='Incorrect password!')
                return render_template('login.html', error='Username not found!')
        except FileNotFoundError:
            return render_template('login.html', error='No users found. Please register first.')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    return render_template('dashboard.html', username=username)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

## ------------------ SAFETY MAP ------------------
DATA_FILE = 'incidents_alerts.csv'
def load_risk_areas():
    risk_areas = []
    with open('incidents_alerts.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            description = row['description'].strip()

            # Assign risk level based on description keywords
            if "GBV" in description or "Rape" in description:
                risk_level = "high"
            elif "Assault" in description or "Theft" in description:
                risk_level = "moderate"
            else:
                risk_level = "low"

            risk_areas.append({
                'risk_level': risk_level,
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'description': description
            })
    return risk_areas
@app.route('/safety-map')
def safety_map():
    username = session.get('username', 'User')
    return render_template('safety_map.html', username=username)
@app.route('/api/risk-areas')
def get_risk_areas():
    data = []
    with open('incidents_alerts.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        print("📂 Looking for CSV file at:", os.path.abspath(DATA_FILE))
        for row in reader:
            data.append({
                'type': row['type'],
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'description': row['description']
            })
    return jsonify(data)

## ------------------ COMMUNITY FORUM ------------------
USERS_CSV = 'users.csv'
CONVERSATIONS_CSV = 'conversations.csv'

def load_users():
    users = []
    with open(USERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({
                'user_id': int(row['user_id']),
                'username': row['username'],
                'online': row['online'],
                'last_seen': row['last_seen']
            })
    return users

def load_conversations():
    convs = []
    with open(CONVERSATIONS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            convs.append({
                'id': int(row['id']),
                'username': row['username'],
                'message': row['message'],
                'timestamp': row['timestamp']
            })
    return convs

@app.route('/community')
def community():
    return render_template('community.html')  # HTML template

@app.route('/api/users')
def get_users():
    with open('users.csv', 'r', encoding='utf-8') as f:
        csv_data = f.read()
    return csv_data

@app.route('/api/conversations')
def get_conversations():
    convs = load_conversations()
    return jsonify(convs)

@app.route('/api/post_message', methods=['POST'])
def post_message():
    data = request.json
    username = data.get('username')
    message = data.get('message')
    # Append to CSV (simulate database)
    with open(CONVERSATIONS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        # generate new id as len + 1
        new_id = sum(1 for _ in open(CONVERSATIONS_CSV))  # naive count
        writer.writerow([new_id, username, message, timestamp])
    return jsonify({'status': 'success'})

PRIVATE_MSG_CSV = 'private_messages.csv'

# Fetch conversations between current user and the selected user
@app.route('/api/private_conversations')
def get_private_conversations():
    user = request.args.get('user')
    sender = request.args.get('sender')
    messages = []
    try:
        with open(PRIVATE_MSG_CSV, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 4:
                    continue
                sender_name, recipient_name, message, timestamp = parts
                if (sender_name == sender and recipient_name == user) or (sender_name == user and recipient_name == sender):
                    messages.append({'sender': sender_name, 'message': message, 'timestamp': timestamp})
    except FileNotFoundError:
        pass
    return jsonify(messages)

# Save a new private message
@app.route('/api/post_private_message', methods=['POST'])
def post_private_message():
    data = request.json
    sender = data['sender']
    recipient = data['recipient']
    message = data['message']
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    with open(PRIVATE_MSG_CSV, 'a', encoding='utf-8') as f:
        f.write(f"{sender},{recipient},{message},{timestamp}\n")
    return jsonify({'status': 'success'})


###
# ------------------ FILE PATHS ------------------
USERS_CSV = "user.csv"
CONTACTS_CSV = "contact.csv"
INCIDENTS_CSV = "incident.csv"
ALERT_SOUND = os.path.join("static", "sounds", "108804__jordanielmills__09-up6.mp3")

# ------------------ CSV HELPERS ------------------
def read_csv(file_path):
    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        return []

def append_csv(file_path, fieldnames, data):
    file_exists = os.path.exists(file_path)
    with open(file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# ------------------ UTILITIES ------------------
def play_dangeralert_sound():
    try:
        if os.path.exists(ALERT_SOUND):
            playsound(ALERT_SOUND)
    except Exception as e:
        print("❌ Sound error:", e)

def get_user_contacts(username):
    contacts = read_csv(CONTACTS_CSV)
    return [
        {"ContactUsername": c["ContactUsername"], "Email": c["Email"]}
        for c in contacts
        if c["Username"].strip().lower() == username.strip().lower()
    ]

def find_nearby_users(username, user_lat, user_lon, radius_km=3):
    users = read_csv(USERS_CSV)
    nearby = []
    for user in users:
        try:
            if user["Username"] == username:
                continue
            lat, lon = float(user["lat"]), float(user["lon"])
            distance = geodesic((user_lat, user_lon), (lat, lon)).km
            if distance <= radius_km:
                nearby.append({
                    "Username": user["Username"],
                    "Email": user["Email"],
                    "Distance_km": round(distance, 2),
                    "OnlineStatus": user.get("OnlineStatus", "Unknown")
                })
        except Exception:
            continue
    return nearby

def notify_contacts(username, incident_type, location):
    contacts = get_user_contacts(username)
    sent_status = []
    print(f"📨 Sending alerts to contacts of {username}: {contacts}")

    for c in contacts:
        contact_email = c.get("Email")
        contact_name = c.get("ContactUsername")

        if not contact_email:
            continue

        subject = f"🚨 DangerAlert: {username} may be in danger!"
        body = (
            f"Dear {contact_name},\n\n"
            f"The DangerAlert system detected a possible {incident_type} incident "
            f"for {username} at location: {location}.\n\n"
            f"Please check on them immediately or contact emergency services.\n\n"
            f"— DangerAlert System"
        )

        try:
            msg = Message(subject, recipients=[contact_email], body=body)
            mail.send(msg)
            print(f"✅ Email sent to {contact_name} ({contact_email})")
            sent_status.append({"contact": contact_name, "email": contact_email, "status": "sent"})
        except Exception as e:
            print(f"❌ Failed to send email to {contact_name}: {e}")
            sent_status.append({"contact": contact_name, "email": contact_email, "status": "failed"})
    return sent_status

def process_emergency(username, location, incident_type, audio_file):
    lat, lon = map(float, location.split(","))
    nearby_users = find_nearby_users(username, lat, lon)
    contacts_alerted = notify_contacts(username, incident_type, location)

    append_csv(
        INCIDENTS_CSV,
        fieldnames=["Timestamp", "User", "Type", "Location", "AudioFile", "Recipients"],
        data={
            "Timestamp": datetime.now().isoformat(),
            "User": username,
            "Type": incident_type,
            "Location": location,
            "AudioFile": audio_file,
            "Recipients": ";".join([c["contact"] for c in contacts_alerted if c["status"] == "sent"])
        }
    )

    play_dangeralert_sound()

    return {
        "status": "processed",
        "incident_type": incident_type,
        "contacts_notified": [c for c in contacts_alerted if c["status"] == "sent"],
        "nearby_users_alerted": nearby_users
    }

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return "✅ Rape Prevention Backend API is running."

@app.route("/emergency_alert")
def emergency_alert_page():
    return render_template("emergency_alert.html", username="User")

@app.route("/api/emergency/trigger", methods=["POST"])
def trigger_emergency():
    try:
        data = request.get_json()
        username = data.get("username")
        location = data.get("location")
        audio_base64 = data.get("audio")

        if not username or not location or not audio_base64:
            return jsonify({"status": "error", "message": "Missing data"}), 400

        os.makedirs("recordings", exist_ok=True)
        audio_path = f"recordings/{username}_{int(time.time())}.wav"
        with open(audio_path, "wb") as f:
            f.write(base64.b64decode(audio_base64))

        # 🔍 Run AI detection
        prediction = ai_model.predict(audio_path)

        if prediction in ["Gender Based Violence", "Rape"]:
            threading.Thread(
                target=process_emergency,
                args=(username, location, prediction, audio_path)
            ).start()

            contacts = get_user_contacts(username)
            nearby = find_nearby_users(username, *map(float, location.split(",")))

            return jsonify({
                "message": f"🚨 {prediction} detected! DangerAlert triggered!",
                "contacts": {"notified_contacts": [c["ContactUsername"] for c in contacts]},
                "nearby": {"notified_nearby": [u["Username"] for u in nearby]}
            }), 200

        else:
            return jsonify({
                "message": "✅ No threat detected.",
                "contacts": {"notified_contacts": []},
                "nearby": {"notified_nearby": []}
            }), 200

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/audio_analysis", methods=["POST"])
def analyze_audio():
    try:
        data = request.get_json()
        username = data.get("username")
        location = data.get("location")
        audio_base64 = data.get("audio")

        if not audio_base64:
            return jsonify({"error": "Missing audio"}), 400

        os.makedirs("temp_audio", exist_ok=True)
        temp_path = f"temp_audio/{username}_{int(time.time())}.wav"
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(audio_base64))

        prediction = ai_model.predict(temp_path)

        return jsonify({
            "prediction": prediction,
            "username": username,
            "location": location
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/incident_reporting")
def incident_reporting_page():
    """Render the incident reporting page."""
    return render_template("incident_reporting.html", username="User")

@app.route("/api/report_incident", methods=["POST"])
def report_incident():
    """Handles user incident report submissions."""
    try:
        data = request.get_json()
        username = data.get("username")
        incident_type = data.get("incident_type")
        description = data.get("description")
        location = data.get("location", "Unknown")
        audio_data = data.get("audio_data")

        if not username or not incident_type or not description:
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        # Save audio evidence if provided
        audio_path = None
        if audio_data:
            os.makedirs("evidence", exist_ok=True)
            audio_path = f"evidence/{username}_{int(time.time())}.wav"
            with open(audio_path, "wb") as f:
                f.write(base64.b64decode(audio_data))

        # Save to incident CSV
        append_csv(
            INCIDENTS_CSV,
            fieldnames=["Timestamp", "User", "Type", "Description", "Location", "AudioFile"],
            data={
                "Timestamp": datetime.now().isoformat(),
                "User": username,
                "Type": incident_type,
                "Description": description,
                "Location": location,
                "AudioFile": audio_path or "None"
            }
        )

        # Send email to police and private security
        recipients = ["police_services@example.com", "security_team@example.com"]
        subject = f"🚨 Incident Report: {incident_type} by {username}"
        body = (
            f"User: {username}\n"
            f"Incident Type: {incident_type}\n"
            f"Description: {description}\n"
            f"Location: {location}\n"
            f"Audio Evidence: {'Attached' if audio_path else 'None'}"
        )

        msg = Message(subject, recipients=recipients, body=body)
        mail.send(msg)

        return jsonify({
            "status": "success",
            "message": "Incident report submitted successfully. Police and security have been notified."
        }), 200

    except Exception as e:
        print("❌ Error in report_incident:", e)
        return jsonify({
            "status": "error",
            "message": f"Failed to submit incident: {str(e)}"
        }), 500

@app.route("/safety_resources")
def safety_resources_page():
    return render_template("safety_resources.html", username="User")

@app.route("/api/safety_resources")
def get_safety_resources():
    return jsonify({
        "support_services": [
            {
                "name": "South African Police Service (SAPS)",
                "description": "24/7 emergency line for crime and safety reports.",
                "contact": "10111",
                "link": "https://www.saps.gov.za/"
            },
            {
                "name": "Gender-Based Violence Command Centre",
                "description": "Support and counseling for GBV victims.",
                "contact": "0800 428 428 / *120*7867#",
                "link": "https://gbv.org.za/"
            },
            {
                "name": "National Suicide Crisis Line",
                "description": "24/7 confidential support for people in emotional distress.",
                "contact": "0800 567 567",
                "link": "https://www.sadag.org/"
            }
        ],
        "educational_materials": [
            {
                "title": "Personal Safety Tips",
                "summary": "Learn practical steps to enhance your safety in daily life.",
                "link": "https://www.saps.gov.za/crimestop/safety_tips.php"
            },
            {
                "title": "Understanding Gender-Based Violence",
                "summary": "Educational material explaining types, causes, and reporting GBV.",
                "link": "https://www.unwomen.org/en/what-we-do/ending-violence-against-women/faqs"
            },
            {
                "title": "Digital Safety & Privacy",
                "summary": "Stay safe online and protect your digital footprint.",
                "link": "https://staysafeonline.org/"
            }
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
