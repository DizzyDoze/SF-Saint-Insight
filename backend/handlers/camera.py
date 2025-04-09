import time
import os
import cv2
import json
from datetime import datetime
from threading import Thread, Lock

from handlers.analyzer import Analyzer
from handlers.detector import YOLOTextDetector


class Camera:
    """Camera manager with YOLO detection and Gemini analysis optimized for classroom use"""

    def __init__(self, llm, analyze_interval=5, headless=True, save_frames=False):
        self.llm = llm
        self.analyze_interval = analyze_interval
        self.last_analysis_time = 0
        self.analyzing = False
        self.running = True
        self.cap = None
        self.results = []
        self.headless = True  # Force headless mode to avoid display issues on macOS
        self.save_frames = save_frames
        self.frame_dir = "captured_frames"
        self.frame_lock = Lock()  # Thread safety for frame processing
        self.results_lock = Lock()  # Additional lock for results

        # Create frames directory if saving is enabled
        if self.save_frames and not os.path.exists(self.frame_dir):
            os.makedirs(self.frame_dir)

        # Use YOLOv8n (nano) model for maximum efficiency
        self.detector = YOLOTextDetector("yolov8n")
        print(f"Camera initialized: headless={self.headless}, save_frames={save_frames}")

    def activate(self):
        """Initialize the camera"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")

            # Print camera properties
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            print(f"Camera activated: {width}x{height} @ {fps}fps")
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False

    def analyze_frame(self, frame):
        """Start a new analysis thread for the current frame"""
        self.analyzing = True
        print("Starting frame analysis...")
        # Create and configure a new analyzer thread
        analyzer = Analyzer("analyzer_thread")
        analyzer.setup(frame, self.llm, self.detector, self.on_analysis_complete)
        analyzer.start()

    def on_analysis_complete(self, results):
        """Callback when analysis finishes"""
        with self.results_lock:
            self.results = results
            self.analyzing = False
            self.last_analysis_time = time.time()

        if results:
            print(f"Analysis complete: {len(results)} objects detected")
            for idx, result in enumerate(results):
                print(f"  {idx + 1}. {result.get('label', 'Unknown')}")
        else:
            print("Analysis complete: No objects detected")

    def process_frame_for_display(self, frame):
        """Process a frame with current analysis results for display"""
        if frame is None:
            return None

        display_frame = frame.copy()

        # Apply results to the frame - always show the latest results
        with self.results_lock:
            current_results = self.results.copy() if self.results else []

        # Draw each result on the frame
        for det in current_results:
            if 'box' in det and 'label' in det:
                box = det['box']
                label = det['label']

                # Draw rectangle
                cv2.rectangle(
                    display_frame,
                    (int(box[0]), int(box[1])),
                    (int(box[2]), int(box[3])),
                    (0, 255, 0),  # Green color in BGR
                    2  # Line thickness
                )

                # Draw label
                cv2.putText(
                    display_frame,
                    label,
                    (int(box[0]), int(box[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        # Add status info
        current_time = time.time()
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

        return display_frame

    def save_frame_with_detections(self, frame):
        """Save the current frame with detections to a file if saving is enabled"""
        if not self.save_frames:
            return None

        try:
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.frame_dir}/frame_{timestamp}.jpg"

            # Save the frame
            cv2.imwrite(filename, frame)
            print(f"Frame saved: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving frame: {e}")
            return None

    def stream(self):
        """Main camera loop - captures frames and handles analysis timing"""
        if not self.activate():
            print("Failed to activate camera. Exiting stream.")
            return

        while self.running:
            try:
                # Capture a frame from the camera
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to capture frame, retrying...")
                    time.sleep(0.5)
                    continue

                # Check if it's time for a new analysis
                current_time = time.time()
                if (current_time - self.last_analysis_time >= self.analyze_interval) and not self.analyzing:
                    print(f"Time for analysis: {current_time - self.last_analysis_time:.2f}s elapsed")
                    self.analyze_frame(frame.copy())

                # Process frame for display or saving
                if self.save_frames and self.results and (current_time - self.last_analysis_time < 2):
                    display_frame = self.process_frame_for_display(frame)
                    self.save_frame_with_detections(display_frame)

                # In headless mode, just process frames without displaying
                time.sleep(0.01)  # Brief sleep to prevent CPU overload

            except Exception as e:
                print(f"Error in camera stream: {e}")
                time.sleep(0.1)  # Prevent tight error loop

        # Clean up resources
        if self.cap is not None:
            self.cap.release()
            print("Camera resources released")