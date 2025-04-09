from threading import Thread
import time
import cv2
from PIL import Image


class Analyzer(Thread):
    """Analyzes frames using YOLO detection and Gemini LLM, optimized for classroom whiteboards"""

    def __init__(self, name):
        super().__init__(name=name)
        self.frame = None
        self.llm = None
        self.callback = None
        self.detector = None  # Will be set by setup

        # Improved prompt specifically for classroom whiteboard analysis
        self.prompt = """
        Analyze this whiteboard image from a classroom setting. Focus on:

        1. Mathematical equations, formulas, or expressions - explain their meaning and applications
        2. Scientific diagrams or charts - describe what they represent
        3. Key concepts, definitions, or terminology - provide clear explanations suitable for students
        4. Any step-by-step procedures or problem-solving methods

        If you see partial writing or unclear content, make reasonable inferences.
        Use student-friendly language and explain concepts at an appropriate level.
        Keep explanations clear, concise, and focused on helping students understand the material.
        """

    def setup(self, frame, llm, detector, callback):
        """Configure the analyzer before starting the thread"""
        self.frame = frame
        self.llm = llm
        self.detector = detector
        self.callback = callback

    def analyze(self):
        """Process the frame with YOLO and Gemini"""
        try:
            print("Starting YOLO detection for classroom whiteboard...")
            # Step 1: Detect regions with YOLO
            regions = self.detector.detect_text(self.frame)

            if not regions:
                print("No regions detected by YOLO")
                # No regions detected
                if self.callback:
                    self.callback([])
                return

            print(f"YOLO detected {len(regions)} regions")

            # For efficiency, let's just analyze the most prominent regions
            # Sort by area (larger regions first)
            sorted_regions = sorted(regions,
                                    key=lambda r: (r['box'][2] - r['box'][0]) * (r['box'][3] - r['box'][1]),
                                    reverse=True)

            # Take at most 2 largest regions to analyze (for efficiency)
            regions_to_analyze = sorted_regions[:min(2, len(sorted_regions))]
            print(f"Analyzing {len(regions_to_analyze)} largest regions")

            enhanced_results = []
            for idx, region in enumerate(regions_to_analyze):
                try:
                    box = region['box']
                    print(f"Processing region {idx + 1}, box: {box}")

                    # Crop the region with a small margin
                    margin = 10
                    x1, y1, x2, y2 = map(int, box)
                    # Ensure boundaries are within frame
                    height, width = self.frame.shape[:2]
                    x1 = max(0, x1 - margin)
                    y1 = max(0, y1 - margin)
                    x2 = min(width, x2 + margin)
                    y2 = min(height, y2 + margin)

                    if x2 <= x1 or y2 <= y1:
                        print(f"Invalid region dimensions: {x1},{y1},{x2},{y2}")
                        continue

                    crop = self.frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        print("Empty crop, skipping region")
                        continue

                    # Convert OpenCV BGR image to PIL RGB image for Gemini
                    pil_crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

                    print(f"Sending whiteboard region {idx + 1} to Gemini API...")
                    # Get analysis from LLM
                    response = self.llm.analyze_image(pil_crop, self.prompt)

                    if response.startswith("Error:"):
                        print(f"Gemini API error for region {idx + 1}: {response}")
                        continue

                    print(f"Received classroom content analysis for region {idx + 1}")

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

                    enhanced_result = {
                        "label": display_label,
                        "box": box,
                        "full_text": response,
                        "region_index": idx,
                        "confidence": region.get('confidence', 0.0)
                    }
                    enhanced_results.append(enhanced_result)

                except Exception as region_error:
                    print(f"Error processing region {idx + 1}: {region_error}")
                    continue

            print(f"Classroom content analysis completed with {len(enhanced_results)} results")
            # Send enhanced results back through callback
            if self.callback:
                self.callback(enhanced_results)

        except Exception as e:
            print(f"Analysis error: {e}")
            if self.callback:
                self.callback([])

    def run(self):
        """Thread execution method"""
        start_time = time.time()
        self.analyze()
        elapsed = time.time() - start_time
        print(f"Classroom whiteboard analysis completed in {elapsed:.2f} seconds")