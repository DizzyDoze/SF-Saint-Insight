import os
from backend.handlers.llm import GeminiWrapper
from backend.handlers.camera import Camera
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# Initialize the application
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not set")
    exit(1)

print("Starting WhiteBoard Scanner with YOLOv8 + Gemini")
print("------------------------------------------------")
print("Press ESC to exit")

# Create system components
llm = GeminiWrapper(api_key)
camera = Camera(llm, analyze_interval=5)  # Process frame every 5 seconds

# Start the camera stream
try:
    camera.stream()
except KeyboardInterrupt:
    camera.running = False

app = Flask(__name__)

@app.route('/')
def home():
    return "Backend is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Expose on all network interfaces