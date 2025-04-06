from threading import Thread

import cv2
from PIL import Image


class Analyzer(Thread):
    """Analyzes frames using YOLO detection and Gemini LLM"""

    def __init__(self, name):
        super().__init__(name=name)
        self.frame = None
        self.llm = None
        self.callback = None
        self.detector = None  # Will be set by setup
        self.prompt = "Analyze this image and describe any visible text content, diagrams, or important objects. Focus on information written on boards or documents."

    def setup(self, frame, llm, detector, callback):
        """Configure the analyzer before starting the thread"""
        self.frame = frame
        self.llm = llm
        self.detector = detector
        self.callback = callback

    def analyze(self):
        """Process the frame with YOLO and Gemini"""
        try:
            # Step 1: Detect regions with YOLO
            regions = self.detector.detect_text(self.frame)

            if not regions:
                # No regions detected
                if self.callback:
                    self.callback([])
                return

            # For efficiency, let's just analyze the most prominent regions
            # Sort by area (larger regions first)
            sorted_regions = sorted(regions,
                                    key=lambda r: (r['box'][2] - r['box'][0]) * (r['box'][3] - r['box'][1]),
                                    reverse=True)

            # Take at most 2 largest regions to analyze (for efficiency)
            regions_to_analyze = sorted_regions[:min(2, len(sorted_regions))]

            enhanced_results = []
            for region in regions_to_analyze:
                box = region['box']

                # Crop the region with a small margin
                margin = 10
                x1, y1, x2, y2 = map(int, box)
                # Ensure boundaries are within frame
                height, width = self.frame.shape[:2]
                x1 = max(0, x1 - margin)
                y1 = max(0, y1 - margin)
                x2 = min(width, x2 + margin)
                y2 = min(height, y2 + margin)

                crop = self.frame[y1:y2, x1:x2]

                # Convert OpenCV BGR image to PIL RGB image for Gemini
                pil_crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

                # Get analysis from LLM
                response = self.llm.analyze_image(pil_crop, self.prompt)

                # Create enhanced result with YOLO box and Gemini interpretation
                enhanced_result = {
                    "label": response[:80],  # Limit to 80 chars for display
                    "box": box,
                    "full_text": response
                }
                enhanced_results.append(enhanced_result)

            # Send enhanced results back through callback
            if self.callback:
                self.callback(enhanced_results)

        except Exception as e:
            print(f"Analysis error: {e}")
            if self.callback:
                self.callback([])

    def run(self):
        """Thread execution method"""
        self.analyze()