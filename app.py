import cv2
import sqlite3
from flask import Flask, Response, render_template_string
from datetime import datetime

app = Flask(name)

def init_db():
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS detections (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT)')
    conn.commit()
    conn.close()

init_db()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) > 0:
            with sqlite3.connect('logs.db') as conn:
                conn.execute("INSERT INTO detections (timestamp) VALUES (?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    try:
        conn = sqlite3.connect('logs.db')
        logs = conn.execute("SELECT * FROM detections ORDER BY id DESC LIMIT 5").fetchall()
        total_count = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        conn.close()
    except:
        logs, total_count = [], 0
    return render_template_string("""
    <html>
        <head><script src="https://cdn.jsdelivr.net/npm/chart.js"></script></head>
        <body style="font-family:sans-serif; background:#121212; color:white; text-align:center;">
            <h1>🛡️ AI Security & DevOps Pipeline</h1>
            <div style="display:flex; justify-content:center; gap:20px;">
                <img src='/video_feed' width='500' style="border:2px solid #00ff00;">
                <div style="background:#1e1e1e; padding:20px; border-radius:10px; border:1px solid #00ff00;">
                    <h3>Total Detections: {{ total_count }}</h3>
                    <canvas id="myChart" width="200" height="200"></canvas>
                </div>
            </div>
            <script>
                new Chart(document.getElementById('myChart'), {
                    type: 'bar',
                    data: { labels: ['Detections'], datasets: [{ label: 'Count', data: [{{ total_count }}], backgroundColor: '#00ff00' }] }
                });
            </script>
        </body>
    </html>
    """, logs=logs, total_count=total_count)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if name == "main":
    app.run(host='0.0.0.0', port=5000)