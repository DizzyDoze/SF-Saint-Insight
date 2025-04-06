import time

import cv2

from backend.handlers.analyzer import Analyzer
from backend.settings import DEFAULT_PROMPT


class Camera:
    def __init__(self, gemini, display, analyze_interval=30):
        self.gemini = gemini
        self.height = None
        self.width = None
        self.cap = None
        self.analyzing = False
        self.analyze_interval = analyze_interval  # Time in seconds between automatic analyses
        self.last_analysis_time = 0
        self.prompt = DEFAULT_PROMPT
        self.running = True
        self.display = display

    def activate(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")

            # Update camera properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False

    def analyze_frame(self, frame):
        """Start a new thread to analyze the frame"""
        # Create and start a new analyzer thread
        analyzer = Analyzer("analyzer_thread")
        analyzer.setup(frame, self.gemini, self.prompt, self.on_analysis_complete)
        analyzer.start()

    def on_analysis_complete(self, results):
        """Callback for when analysis is complete"""
        self.display.update_results(results)
        self.analyzing = False

    def stream(self):
        """Main loop for camera streaming and periodic analysis"""
        if not self.activate():
            return

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Check if it's time for automatic analysis
            current_time = time.time()
            if (current_time - self.last_analysis_time >= self.analyze_interval) and not self.analyzing:
                self.analyze_frame(frame)

            # Display frame with overlay
            display_frame = self.display.overlay_on_frame(frame)
            cv2.imshow('Camera Feed', display_frame)

            # Check for exit command (ESC key)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                self.running = False

        # Release resources
        self.cap.release()
        cv2.destroyAllWindows()
