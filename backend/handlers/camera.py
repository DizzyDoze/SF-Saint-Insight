import time

import cv2

from backend.handlers.analyzer import Analyzer
from backend.handlers.detector import YOLOTextDetector


class Camera:
    """Camera manager with YOLO detection and Gemini analysis"""

    def __init__(self, llm, analyze_interval=5):
        self.llm = llm
        self.analyze_interval = analyze_interval
        self.last_analysis_time = 0
        self.analyzing = False
        self.running = True
        self.cap = None
        self.results = []
        # Use YOLOv8n (nano) model for maximum efficiency
        self.detector = YOLOTextDetector("yolov8n")

    def activate(self):
        """Initialize the camera"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False

    def analyze_frame(self, frame):
        """Start a new analysis thread for the current frame"""
        self.analyzing = True
        # Create and configure a new analyzer thread
        analyzer = Analyzer("analyzer_thread")
        analyzer.setup(frame, self.llm, self.detector, self.on_analysis_complete)
        analyzer.start()

    def on_analysis_complete(self, results):
        """Callback when analysis finishes"""
        self.results = results
        self.analyzing = False
        self.last_analysis_time = time.time()

    def stream(self):
        """Main camera loop - captures frames and handles analysis timing"""
        if not self.activate():
            return

        while self.running:
            # Capture a frame from the camera
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Check if it's time for a new analysis
            current_time = time.time()
            if (current_time - self.last_analysis_time >= self.analyze_interval) and not self.analyzing:
                self.analyze_frame(frame)

            # Visualize results directly using detector
            display_frame = self.detector.visualize(frame, self.results)

            # Add status info
            status = "Analyzing..." if self.analyzing else f"Next analysis in {int(self.analyze_interval - (current_time - self.last_analysis_time))}s"
            cv2.putText(
                display_frame,
                status,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),  # Red color
                2
            )

            cv2.imshow('Smart Analyzer', display_frame)

            # Check for ESC key to exit
            if cv2.waitKey(1) & 0xFF == 27:
                self.running = False

        # Clean up resources
        self.cap.release()
        cv2.destroyAllWindows()