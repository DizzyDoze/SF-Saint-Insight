import base64
import os
import threading
import time

import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from handlers.detector import YOLOTextDetector
from handlers.llm import GeminiWrapper

load_dotenv()

# Initialize the application
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not set")
    exit(1)

app = Flask(__name__)
# Enable CORS with additional configuration for larger payloads
CORS(app, resources={r"/*": {"origins": "*", "max_age": 86400}})

# Global variables
frame_lock = threading.Lock()
results_lock = threading.Lock()
is_analyzing = False

# Initialize Gemini and YOLO detector
llm = GeminiWrapper(api_key)
detector = YOLOTextDetector("yolov8n")  # Initialize the YOLO detector

# Analysis prompt
ANALYSIS_PROMPT = """
Analyze this whiteboard image from a classroom setting. Focus on:

1. Mathematical equations, formulas, or expressions - explain their meaning and applications
2. Scientific diagrams or charts - describe what they represent
3. Key concepts, definitions, or terminology - provide clear explanations suitable for students
4. Any step-by-step procedures or problem-solving methods

If you see partial writing or unclear content, make reasonable inferences.
Use student-friendly language and explain concepts at an appropriate level.
Keep explanations clear, concise, and focused on helping students understand the material.
"""


def analyze_region(img, box, region_index):
    """Analyze a specific region of the image"""
    try:
        # Extract coordinates
        x1, y1, x2, y2 = map(int, box)

        # Ensure boundaries are within frame
        h, w = img.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # Skip invalid regions
        if x2 <= x1 or y2 <= y1:
            print(f"Invalid region dimensions: {x1},{y1},{x2},{y2}")
            return None

        # Crop the region
        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            print("Empty crop, skipping region")
            return None

        # Convert OpenCV BGR to PIL RGB
        pil_crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

        # Get analysis from LLM
        print(f"Sending whiteboard region {region_index} to Gemini API...")
        response = llm.analyze_image(pil_crop, ANALYSIS_PROMPT)

        if response.startswith("Error:"):
            print(f"Gemini API error for region {region_index}: {response}")
            return None

        print(f"Received content analysis for region {region_index}")

        # Create enhanced result with YOLO box and Gemini interpretation
        subject_marker = ""
        if "math" in response.lower() or "equation" in response.lower():
            subject_marker = "📐 "
        elif "science" in response.lower() or "physics" in response.lower():
            subject_marker = "🔬 "
        elif "history" in response.lower() or "date" in response.lower():
            subject_marker = "📜 "
        elif "english" in response.lower() or "literature" in response.lower():
            subject_marker = "📚 "

        # Create a concise label for display
        if len(response) > 80:
            display_label = subject_marker + response[:77] + "..."
        else:
            display_label = subject_marker + response

        # Calculate normalized boundingBox for frontend
        img_height, img_width = img.shape[:2]

        boundingBox = {
            "x": float(x1) / img_width,
            "y": float(y1) / img_height,
            "width": float(x2 - x1) / img_width,
            "height": float(y2 - y1) / img_height
        }

        # Return the analysis result
        return {
            "id": region_index + 1,
            "title": subject_marker + "Whiteboard Analysis",
            "fact": response if len(response) < 100 else response[:97] + "...",
            "full_text": response,
            "boundingBox": boundingBox,
            "confidence": 1.0  # Default confidence
        }

    except Exception as e:
        print(f"Error analyzing region {region_index}: {e}")
        return None


# New API endpoint for processing images from React frontend
@app.route('/process_image', methods=['POST'])
def process_image():
    """Process an image sent from the React frontend"""
    global is_analyzing
    try:
        # Check if already analyzing
        if is_analyzing:
            return jsonify({
                "status": "busy",
                "message": "Already processing an image"
            }), 429  # 429 Too Many Requests

        is_analyzing = True

        # Get start time for performance tracking
        start_time = time.time()
        print("Received image processing request")

        # Get the base64 image from the request
        data = request.json
        if not data or 'image' not in data:
            is_analyzing = False
            return jsonify({
                "status": "error",
                "message": "No image data provided"
            }), 400

        # Decode the base64 image
        try:
            image_data = base64.b64decode(data['image'])
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            is_analyzing = False
            print(f"Error decoding image: {e}")
            return jsonify({
                "status": "error",
                "message": "Could not decode image"
            }), 400

        if img is None:
            is_analyzing = False
            return jsonify({
                "status": "error",
                "message": "Could not decode image"
            }), 400

        # Log image dimensions
        h, w = img.shape[:2]
        print(f"Processing image: {w}x{h} pixels")

        # Step 1: Detect regions with YOLO
        print("Running YOLO detection...")
        regions = detector.detect_text(img)

        if not regions:
            print("No regions detected by YOLO")
            # If no regions detected, analyze the whole image
            h, w = img.shape[:2]
            regions = [{"label": "Full Frame", "box": [0, 0, w, h]}]

        print(f"YOLO detected {len(regions)} regions")

        # Sort regions by area (larger regions first)
        sorted_regions = sorted(regions,
                                key=lambda r: (r['box'][2] - r['box'][0]) * (r['box'][3] - r['box'][1]),
                                reverse=True)

        # Take at most 2 largest regions to analyze (for efficiency)
        regions_to_analyze = sorted_regions[:min(2, len(sorted_regions))]
        print(f"Analyzing {len(regions_to_analyze)} largest regions")

        # Analyze each region
        detections = []
        for idx, region in enumerate(regions_to_analyze):
            box = region['box']
            print(f"Processing region {idx + 1}, box: {box}")

            result = analyze_region(img, box, idx)
            if result:
                detections.append(result)

        # If no successful detections, fallback to analyzing the whole image
        if not detections:
            print("No successful region analyses, analyzing whole image")
            # Convert OpenCV BGR to PIL RGB
            pil_image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            # Send to Gemini API
            print("Sending full image to Gemini API...")
            response = llm.analyze_image(pil_image, ANALYSIS_PROMPT)

            if not response.startswith("Error:"):
                # Format the response for the frontend
                subject_marker = ""
                if "math" in response.lower() or "equation" in response.lower():
                    subject_marker = "📐 "
                elif "science" in response.lower() or "physics" in response.lower():
                    subject_marker = "🔬 "

                detections = [{
                    "id": 1,
                    "title": subject_marker + "Whiteboard Analysis",
                    "fact": response if len(response) < 100 else response[:97] + "...",
                    "full_text": response,
                    "boundingBox": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8}
                }]

        # Log processing time
        elapsed_time = time.time() - start_time
        print(f"Analysis completed in {elapsed_time:.2f} seconds with {len(detections)} detections")

        # Return detections in the format expected by the frontend
        return jsonify({
            "status": "success",
            "processingTime": elapsed_time,
            "detections": detections
        })

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error processing image: {str(e)}"
        }), 500
    finally:
        is_analyzing = False


@app.route('/api/status', methods=['GET'])
def api_status():
    """Simple API status endpoint"""
    return jsonify({
        "status": "online",
        "message": "Classroom Whiteboard Analyzer API is running",
        "version": "1.0.0"
    })


@app.route('/')
def home():
    """Return API status at the root path instead of HTML template"""
    return jsonify({
        "service": "Classroom Whiteboard Analyzer API",
        "status": "running",
        "endpoints": {
            "/process_image": "POST - Analyze a whiteboard image",
            "/api/status": "GET - Check API status"
        }
    })


if __name__ == '__main__':
    # Use a higher worker timeout for handling larger images
    app.run(host='0.0.0.0', port=8888, debug=True, threaded=True)