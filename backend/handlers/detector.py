import cv2
from ultralytics import YOLO


class YOLOTextDetector:
    """Text detection using standard YOLO model for efficiency"""

    def __init__(self, model_name="yolov8n"):
        """Initialize with a standard YOLO model"""
        try:
            # Use the standard YOLOv8 nano model (smallest and fastest)
            self.model = YOLO(model_name)
            print(f"YOLO model loaded: {model_name}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None

    def detect_text(self, frame):
        """Detect potential text regions or objects in the frame"""
        if self.model is None:
            return []

        try:
            # Run YOLO detection on the frame
            results = self.model(frame, conf=0.3)  # Slightly higher confidence threshold

            # Classes that might contain text or are of interest
            text_related_classes = [
                'person', 'book', 'tv', 'laptop', 'cell phone', 'keyboard',
                'whiteboard', 'screen', 'monitor', 'document', 'paper'
            ]

            # Convert YOLO results to similar format as Gemini
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get coordinates (convert to [x1, y1, x2, y2] format)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Get class name and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = result.names[cls]

                    # Filter for potentially interesting objects
                    # Or keep all objects if we're not getting many detections
                    if len(boxes) < 3 or cls_name.lower() in text_related_classes:
                        detection = {
                            "label": f"{cls_name} ({conf:.2f})",
                            "box": [x1, y1, x2, y2],
                            "confidence": conf
                        }
                        detections.append(detection)

            # If no detections, divide the frame into regions as a fallback
            if not detections:
                # Just analyze the whole frame
                h, w = frame.shape[:2]
                detections = [{"label": "Full Frame", "box": [0, 0, w, h]}]

            return detections
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return []

    def visualize(self, frame, detections):
        """Draw bounding boxes and labels on the frame"""
        result_frame = frame.copy()

        for det in detections:
            if 'box' in det and 'label' in det:
                box = det['box']
                label = det['label']

                # Draw rectangle
                cv2.rectangle(
                    result_frame,
                    (int(box[0]), int(box[1])),
                    (int(box[2]), int(box[3])),
                    (0, 255, 0),  # Green color in BGR
                    2  # Line thickness
                )

                # Draw label
                cv2.putText(
                    result_frame,
                    label,
                    (int(box[0]), int(box[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        return result_frame