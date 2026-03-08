"""
SafeLink AI - Fast Background Monitor (LBPH Face Recognizer)
=============================================================
Detects shoulder surfing using LBPH face recognition and HOG person detection.
Runs in background with alert-triggered display.
"""

import cv2
import numpy as np
import threading
import time
from plyer import notification

class SafeLinkMonitor:
    """
    Background monitor for shoulder surfing detection using LBPH face recognition.
    """
    
    def __init__(self):
        self.running = False
        self.alert_active = False
        self.last_notification_time = 0
        self.notification_cooldown = 10  # seconds
        
        # Performance optimization: frame skip counter
        self.frame_index = 0
        self.detect_every_n_frames = 3
        
        # Detection results (shared between threads)
        self.current_status = "INITIALIZING"
        self.owner_count = 0
        self.unknown_count = 0
        self.people_behind = 0
        
        # Load LBPH Face Recognizer model
        print("[SafeLink AI] Loading owner recognition model...")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        try:
            self.recognizer.read("owner_model.yml")
            print("[SafeLink AI] Owner model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load owner_model.yml: {e}")
            print("[ERROR] Please run register_owner_lbph.py first")
            exit(1)
        
        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Initialize HOG detector for person detection (behind user)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("[ERROR] Cannot access webcam")
            exit(1)
        
        print("[SafeLink AI] System started")
        print("[SafeLink AI] Fast background monitoring active")
    
    def send_notification(self, title, message):
        """
        Send desktop notification with cooldown to prevent spam.
        """
        current_time = time.time()
        if current_time - self.last_notification_time > self.notification_cooldown:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="SafeLink AI",
                    timeout=5
                )
                self.last_notification_time = current_time
            except Exception as e:
                print(f"[WARNING] Notification failed: {e}")
    
    def detect_shoulder_surfing(self, frame, frame_small):
        """
        Detect faces and people in frame.
        Returns: (owner_count, unknown_count, people_behind, face_boxes, person_boxes)
        """
        owner_count = 0
        unknown_count = 0
        face_boxes = []
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar Cascade (on small frame for speed)
        faces_small = self.face_cascade.detectMultiScale(
            gray_small,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40)  # Adjusted for smaller frame
        )
        
        # Process each detected face
        for (x_s, y_s, w_s, h_s) in faces_small:
            # Scale coordinates back to original frame size
            x, y, w, h = x_s*2, y_s*2, w_s*2, h_s*2
            
            # Extract and prepare face for recognition
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (200, 200))
            
            # Predict using LBPH recognizer
            label, confidence = self.recognizer.predict(face_resized)
            
            # Confidence threshold: < 70 = owner, >= 70 = unknown
            if confidence < 70:
                owner_count += 1
                face_boxes.append((x, y, w, h, "OWNER", confidence))
            else:
                unknown_count += 1
                face_boxes.append((x, y, w, h, "UNKNOWN", confidence))
        
        # Detect people (full body) using HOG - detects people behind user
        people_behind = 0
        person_boxes = []
        
        try:
            # HOG detection on small frame for performance
            people, weights = self.hog.detectMultiScale(
                frame_small,
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )
            
            # Only count people not already detected as faces
            for (x_s, y_s, w_s, h_s) in people:
                # Scale back to original size
                x, y, w, h = x_s*2, y_s*2, w_s*2, h_s*2
                
                # Check if this person box overlaps with a face box
                is_face = False
                for (fx, fy, fw, fh, _, _) in face_boxes:
                    if self._boxes_overlap((x, y, w, h), (fx, fy, fw, fh)):
                        is_face = True
                        break
                
                if not is_face:
                    people_behind += 1
                    person_boxes.append((x, y, w, h))
        except Exception as e:
            pass  # HOG detection can fail, continue anyway
        
        return owner_count, unknown_count, people_behind, face_boxes, person_boxes
    
    def _boxes_overlap(self, box1, box2):
        """Check if two bounding boxes overlap."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)
    
    def background_monitor(self):
        """
        Background monitoring thread.
        Continuously analyzes webcam feed and triggers alerts.
        """
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            self.frame_index += 1
            
            # Performance optimization: resize frame for faster processing
            frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Detect only every N frames to reduce CPU usage
            if self.frame_index % self.detect_every_n_frames == 0:
                owner_cnt, unknown_cnt, people_cnt, _, _ = self.detect_shoulder_surfing(frame, frame_small)
                
                # Update shared state
                self.owner_count = owner_cnt
                self.unknown_count = unknown_cnt
                self.people_behind = people_cnt
                
                # Determine security status
                total_threats = unknown_cnt + people_cnt
                
                if owner_cnt == 1 and total_threats == 0:
                    self.current_status = "SAFE"
                    self.alert_active = False
                elif owner_cnt == 0 and total_threats == 0:
                    self.current_status = "NO PERSON DETECTED"
                    self.alert_active = False
                else:
                    self.current_status = "⚠ SHOULDER SURFING DETECTED"
                    self.alert_active = True
                    
                    # Send notification
                    self.send_notification(
                        "⚠ SafeLink AI Alert",
                        "Another person detected looking at your screen."
                    )
            
            # Small delay to prevent CPU overload
            time.sleep(0.03)
    
    def display_monitor(self):
        """
        Display live monitor window when alerts are active or on demand.
        """
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Performance optimization: resize for faster processing
            frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Detect on current frame
            if self.frame_index % self.detect_every_n_frames == 0:
                owner_cnt, unknown_cnt, people_cnt, face_boxes, person_boxes = \
                    self.detect_shoulder_surfing(frame, frame_small)
            else:
                # Use cached results between detections
                face_boxes = []
                person_boxes = []
            
            # Read fresh frame data for each detection
            if self.frame_index % self.detect_every_n_frames == 0:
                owner_cnt, unknown_cnt, people_cnt, face_boxes, person_boxes = \
                    self.detect_shoulder_surfing(frame, frame_small)
                
                # Draw face boxes
                for (x, y, w, h, person_type, confidence) in face_boxes:
                    if person_type == "OWNER":
                        color = (0, 255, 0)  # Green for owner
                        label = f"OWNER ({confidence:.0f})"
                    else:
                        color = (0, 0, 255)  # Red for unknown
                        label = f"INTRUDER ({confidence:.0f})"
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, label, (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Draw person boxes (people behind user)
                for (x, y, w, h) in person_boxes:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 165, 255), 2)  # Orange
                    cv2.putText(frame, "PERSON BEHIND", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            # Draw status panel
            self._draw_status_panel(frame)
            
            # Display frame
            cv2.imshow("SafeLink AI Monitor", frame)
            
            # Check for Q key to exit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[SafeLink AI] Stopping monitor...")
                self.running = False
                break
    
    def _draw_status_panel(self, frame):
        """
        Draw status information panel on frame.
        """
        h, w = frame.shape[:2]
        
        # Semi-transparent dark background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (w-10, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Status text color
        if "SHOULDER SURFING" in self.current_status:
            status_color = (0, 0, 255)  # Red
        elif self.current_status == "SAFE":
            status_color = (0, 255, 0)  # Green
        else:
            status_color = (200, 200, 200)  # Gray
        
        # Main status text
        cv2.putText(frame, self.current_status, (20, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)
        
        # Detection counts
        info_text = f"Owner: {self.owner_count} | Unknown: {self.unknown_count} | Behind: {self.people_behind}"
        cv2.putText(frame, info_text, (20, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Exit instruction
        cv2.putText(frame, "Press Q to exit", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    
    def start(self):
        """
        Start the monitoring system.
        """
        self.running = True
        
        # Start background monitoring thread
        monitor_thread = threading.Thread(target=self.background_monitor, daemon=True)
        monitor_thread.start()
        
        # Run display in main thread
        self.display_monitor()
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        print("[SafeLink AI] System stopped")

if __name__ == "__main__":
    monitor = SafeLinkMonitor()
    monitor.start()
