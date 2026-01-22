import cv2  # Computer Vision (AI) အတွက် သုံးတဲ့ Library
import sqlite3  # အချက်အလက်တွေ သိမ်းဖို့ Database Library
from flask import Flask, Response, render_template_string # Web Dashboard အတွက်
from datetime import datetime # အချိန် မှတ်တမ်းတင်ရန်

# (၁) ဤနေရာတွင် __name__ ဟု ပြင်ဆင်ထားပါသည်
app = Flask(__name__)

# --- အဆင့် (၁) Database တည်ဆောက်ခြင်း ---
def init_db():
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS detections 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db() 

# --- အဆင့် (၂) AI Model Load လုပ်ခြင်း ---
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# --- အဆင့် (၃) Camera နှင့် AI Logic ---
def generate_frames():
    camera = cv2.VideoCapture(0) 
    while True:
        success, frame = camera.read() 
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                with sqlite3.connect('logs.db') as conn:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn.execute("INSERT INTO detections (timestamp) VALUES (?)", (current_time,))
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Person Detected", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- အဆင့် (၄) Web Dashboard (Frontend) ---
@app.route('/')
def index():
    try:
        conn = sqlite3.connect('logs.db')
        logs = conn.execute("SELECT * FROM detections ORDER BY id DESC LIMIT 5").fetchall()
        total_count = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        conn.close()
    except:
        logs = []
        total_count = 0
    
    # HTML နှင့် UI ကို ပိုမိုလှပအောင် ပေါင်းစပ်ပေးထားပါသည်
    return render_template_string("""
    <html>
        <head>
            <title>AI Security Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #121212; color: white; text-align: center; padding: 20px; }
                .container { display: flex; justify-content: center; gap: 30px; margin-top: 20px; }
                .box { background: #1e1e1e; padding: 20px; border-radius: 15px; border: 2px solid #00ff00; width: 45%; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { border: 1px solid #333; padding: 10px; }
                th { background: #00ff00; color: black; }
            </style>
        </head>
        <body>
            <h1>🛡️ Advanced AI Surveillance & DevOps Pipeline</h1>
            <div class="container">
                <div class="box">
                    <h3>Live Video Feed</h3>
                    <img src='/video_feed' width='100%' style="border-radius: 10px; border: 2px solid #555;">
                </div>
                <div class="box">
                    <h3>Security Analytics</h3>
                    <p>Total Detections: <strong style="color: #00ff00; font-size: 24px;">{{ total_count }}</strong></p>
                    <table>
                        <tr><th>Recent Detection Logs (Time)</th></tr>
                        {% for log in logs %}
                        <tr><td>⏰ {{ log[1] }}</td></tr>
                        {% endfor %}
                    </table>
                    <div style="width: 100%; margin-top: 20px;">
                        <canvas id="myChart"></canvas>
                    </div>
                </div>
            </div>
            <script>
                var ctx = document.getElementById('myChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: { 
                        labels: ['Detections'], 
                        datasets: [{ 
                            label: 'Frequency', 
                            data: [{{ total_count }}], 
                            backgroundColor: '#00ff00' 
                        }] 
                    },
                    options: { scales: { y: { beginAtZero: true } } }
                });
            </script>
        </body>
    </html>
    """, logs=logs, total_count=total_count)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# (၂) ဤနေရာတွင် __name__ နှင့် "__main__" ဟု ပြင်ဆင်ထားပါသည်
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)