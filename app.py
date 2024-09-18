from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, abort, send_from_directory
import json
import os
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USER_DATA_FILE = 'data/users.json'
UPLOAD_FOLDER = 'static/profile_pics'
VIDEO_FOLDER = 'static/videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# Ensure the data directory and user file exist
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
if not os.path.isfile(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def generate_unique_url(existing_urls, length=10):
    while True:
        url = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if url not in existing_urls:
            return url

@app.route('/')
def home():
    users = load_users()
    videos = []
    for user in users.values():
        if 'videos' in user:
            videos.extend(user['videos'])
    # Randomly shuffle videos and take a subset if needed
    random.shuffle(videos)
    return render_template('home.html', videos=videos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        profile_pic = request.files.get('profile_pic')
        
        users = load_users()

        if username in users:
            return "Username already taken"

        # Generate unique channel URL
        existing_urls = {user.get('channel_url') for user in users.values() if 'channel_url' in user}
        channel_url = generate_unique_url(existing_urls)
        
        # Save user data
        user_data = {
            'password': password,
            'channel_url': channel_url,
            'profile_pic': '',
            'videos': []
        }

        # Save profile picture
        if profile_pic and profile_pic.filename:
            profile_pic_path = os.path.join(UPLOAD_FOLDER, f"{username}.jpg")
            profile_pic.save(profile_pic_path)
            user_data['profile_pic'] = f"profile_pics/{username}.jpg"

        users[username] = user_data
        save_users(users)
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return "Invalid username or password"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/profile_pics/<filename>')
def profile_pics(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/videos/<filename>')
def videos(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route('/<channel_url>')
def channel(channel_url):
    users = load_users()
    user = next((u for u in users.values() if u['channel_url'] == channel_url), None)
    if user:
        return render_template('channel.html', user=user, channel_url=channel_url)
    abort(404)

@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        video_file = request.files.get('video')

        if video_file and video_file.filename:
            # Ensure the file has a secure name
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(VIDEO_FOLDER, filename)
            video_file.save(video_path)

            users = load_users()
            username = session['username']

            if username in users:
                if 'videos' not in users[username]:
                    users[username]['videos'] = []
                users[username]['videos'].append(f'videos/{filename}')
                save_users(users)

            return redirect(url_for('channel', channel_url=users[username]['channel_url']))

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True, port=4565)
