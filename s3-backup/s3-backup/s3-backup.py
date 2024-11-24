from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Welcome to the Home Assistant Flask Add-on!"

@app.route("/api/hello", methods=['GET'])
def hello():
    return jsonify(message="Hello from the Flask Add-on!")

if __name__ == "__main__":
    # This block will not be executed by Gunicorn
    app.run(host="0.0.0.0", port=5000)