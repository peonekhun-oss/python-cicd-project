from flask import Flask
app = Flask(name)

@app.route('/')
def home():
    return "<h1>Project: Automated CI/CD Pipeline</h1><p>Status: Running Successfully</p>"

if name == "main":
    app.run(host='0.0.0.0', port=5000)