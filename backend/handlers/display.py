import threading

import cv2


class Display:
    """Handles visualization of analysis results on video frames"""

    def __init__(self):
        # Thread-safe storage for analysis results
        self.results = []
        self.lock = threading.Lock()  # Prevents race conditions

    def update_results(self, results):
        """Thread-safe method to update results"""
        with self.lock:
            self.results = results

    def overlay_on_frame(self, frame):
        """Draw bounding boxes and labels on the frame"""
        with self.lock:  # Lock while accessing shared data
            if not self.results:
                return frame

            result_frame = frame.copy()

            # Draw each detection on the frame
            for result in self.results:
                if isinstance(result, dict) and 'label' in result and 'box' in result:
                    label = result['label']
                    box = result['box']  # [x1, y1, x2, y2]

                    # Draw green rectangle
                    cv2.rectangle(
                        result_frame,
                        (int(box[0]), int(box[1])),
                        (int(box[2]), int(box[3])),
                        (0, 255, 0),  # Green color in BGR
                        2  # Line thickness
                    )

                    # Draw text label above box
                    cv2.putText(
                        result_frame,
                        label,
                        (int(box[0]), int(box[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,  # Font scale
                        (0, 255, 0),  # Green color
                        2  # Line thickness
                    )

            return result_frame