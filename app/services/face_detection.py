"""Face Detection and Analysis Service using face_recognition (with optional MediaPipe)"""

from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np
import face_recognition
from app.core.config import settings

# MediaPipe is optional - will use fallback methods if not available
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️  MediaPipe not available - using OpenCV fallback for facial landmarks")


class FaceDetectionService:
    """Service for face detection, landmark detection, and facial analysis"""
    
    def __init__(self):
        # Initialize MediaPipe Face Mesh if available
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=settings.mediapipe_min_detection_confidence,
                min_tracking_confidence=settings.mediapipe_min_tracking_confidence
            )
            
            # Initialize MediaPipe Drawing
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
        else:
            self.face_mesh = None
        
        # Face detection settings
        self.min_face_percentage = settings.min_face_percentage
        self.max_face_percentage = settings.max_face_percentage
        self.max_tilt_angle = settings.max_tilt_angle_degrees
    
    def analyze_face(self, image: np.ndarray) -> Dict:
        """
        Perform comprehensive face analysis.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            Dictionary with face analysis results
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "face_detected": False,
            "metrics": {}
        }
        
        # Detect faces using face_recognition library
        face_locations = self.detect_faces(image)
        
        if not face_locations:
            results["is_valid"] = False
            results["errors"].append("No face detected in image")
            return results
        
        if len(face_locations) > 1:
            results["is_valid"] = False
            results["errors"].append(f"Multiple faces detected ({len(face_locations)}). Only one person should be in the photo")
            return results
        
        results["face_detected"] = True
        face_location = face_locations[0]
        
        # Get face bounding box
        top, right, bottom, left = face_location
        results["metrics"]["face_location"] = {
            "top": int(top),
            "right": int(right),
            "bottom": int(bottom),
            "left": int(left)
        }
        
        # Check face size percentage
        face_percentage = self.calculate_face_percentage(image, face_location)
        results["metrics"]["face_percentage"] = face_percentage
        
        if face_percentage < self.min_face_percentage:
            results["is_valid"] = False
            results["errors"].append(
                f"Face is too small ({face_percentage:.1f}%). Face should occupy {self.min_face_percentage}-{self.max_face_percentage}% of the image"
            )
        elif face_percentage > self.max_face_percentage:
            results["is_valid"] = False
            results["errors"].append(
                f"Face is too large ({face_percentage:.1f}%). Face should occupy {self.min_face_percentage}-{self.max_face_percentage}% of the image"
            )
        
        # Check face centering
        is_centered, offset = self.check_face_centering(image, face_location)
        results["metrics"]["is_centered"] = is_centered
        results["metrics"]["center_offset_percentage"] = offset
        
        if not is_centered:
            results["warnings"].append(
                f"Face is not centered (offset: {offset:.1f}%)"
            )
        
        # Analyze with MediaPipe for detailed landmarks (if available)
        if self.face_mesh:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_results = self.face_mesh.process(rgb_image)
            
            if mp_results.multi_face_landmarks:
                face_landmarks = mp_results.multi_face_landmarks[0]
                
                # Check head tilt
                tilt_angle = self.calculate_head_tilt(face_landmarks, image.shape)
                results["metrics"]["head_tilt_degrees"] = abs(tilt_angle)
                
                if abs(tilt_angle) > self.max_tilt_angle:
                    results["is_valid"] = False
                    results["errors"].append(
                        f"Head is tilted ({abs(tilt_angle):.1f}°). Maximum allowed tilt: {self.max_tilt_angle}°"
                    )
                
                # Check eyes visibility and state
                eyes_analysis = self.analyze_eyes(face_landmarks, image.shape)
                results["metrics"]["eyes"] = eyes_analysis
                
                if not eyes_analysis["both_eyes_visible"]:
                    results["is_valid"] = False
                    results["errors"].append("Both eyes must be clearly visible")
                
                if eyes_analysis["eyes_closed"]:
                    results["is_valid"] = False
                    results["errors"].append("Eyes must be open")
                
                # Check gaze direction
                gaze = self.analyze_gaze_direction(face_landmarks, image.shape)
                results["metrics"]["gaze"] = gaze
                
                if not gaze["looking_at_camera"]:
                    results["is_valid"] = False
                    results["errors"].append("Person must be looking directly at the camera")
                
                # Check mouth state
                mouth_open = self.check_mouth_open(face_landmarks, image.shape)
                results["metrics"]["mouth_open"] = mouth_open
                
                if mouth_open:
                    results["is_valid"] = False
                    results["errors"].append("Mouth must be closed")
        else:
            # MediaPipe not available - add warning
            results["warnings"].append(
                "Advanced facial landmark analysis unavailable (MediaPipe not installed). "
                "Some ICAO compliance checks are limited."
            )
        
        return results
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using face_recognition library.
        
        Args:
            image: Image as numpy array in BGR format
            
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(
            rgb_image, 
            model=settings.face_recognition_model
        )
        return face_locations
    
    def calculate_face_percentage(self, image: np.ndarray, 
                                  face_location: Tuple[int, int, int, int]) -> float:
        """
        Calculate what percentage of the image the head occupies.
        
        Per ICAO 9303 standards, measurement should be from top of head to top of shoulders,
        not just the face detection box (which typically goes from forehead to chin).
        
        Face detection libraries typically detect the face area (forehead to chin), but ICAO
        requires "head and top of shoulders" which is typically 1.3-1.5x the face height.
        
        We extend the detected face box to approximate the full head + shoulders measurement:
        - Add 30% above (to include hair/top of head)
        - Add 20% below (to include chin to shoulder area)
        
        Args:
            image: Image as numpy array
            face_location: Face bounding box (top, right, bottom, left)
            
        Returns:
            Percentage of image height occupied by head + shoulders
        """
        top, right, bottom, left = face_location
        face_height = bottom - top
        
        # ICAO measures "head and top of shoulders", not just face detection box
        # Face detection typically captures forehead to chin
        # We need to account for:
        # - Hair/top of head (add ~30% above detected face)
        # - Chin to shoulders (add ~20% below detected face)
        head_and_shoulders_height = face_height * 1.5  # 1.0 + 0.3 + 0.2
        
        image_height = image.shape[0]
        
        # Calculate head+shoulders height as percentage of image height (ICAO standard)
        percentage = (head_and_shoulders_height / image_height) * 100
        
        return percentage
    
    def check_face_centering(self, image: np.ndarray, 
                            face_location: Tuple[int, int, int, int]) -> Tuple[bool, float]:
        """
        Check if face is centered in the image.
        
        Args:
            image: Image as numpy array
            face_location: Face bounding box (top, right, bottom, left)
            
        Returns:
            Tuple of (is_centered, offset_percentage)
        """
        img_height, img_width = image.shape[:2]
        img_center_x = img_width / 2
        img_center_y = img_height / 2
        
        top, right, bottom, left = face_location
        face_center_x = (left + right) / 2
        face_center_y = (top + bottom) / 2
        
        # Calculate offset from center
        offset_x = abs(face_center_x - img_center_x) / img_width * 100
        offset_y = abs(face_center_y - img_center_y) / img_height * 100
        
        # Face is considered centered if offset is less than 15%
        is_centered = offset_x < 15 and offset_y < 15
        max_offset = max(offset_x, offset_y)
        
        return is_centered, max_offset
    
    def calculate_head_tilt(self, face_landmarks, image_shape: Tuple[int, int, int]) -> float:
        """
        Calculate head tilt angle using eye landmarks.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            image_shape: Shape of the image (height, width, channels)
            
        Returns:
            Tilt angle in degrees (positive = tilted right, negative = tilted left)
        """
        height, width = image_shape[:2]
        
        # Get eye landmarks (left and right eye outer corners)
        # Left eye outer corner: landmark 33
        # Right eye outer corner: landmark 263
        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        
        # Convert normalized coordinates to pixel coordinates
        left_eye_x = left_eye.x * width
        left_eye_y = left_eye.y * height
        right_eye_x = right_eye.x * width
        right_eye_y = right_eye.y * height
        
        # Calculate angle
        delta_y = right_eye_y - left_eye_y
        delta_x = right_eye_x - left_eye_x
        angle = np.degrees(np.arctan2(delta_y, delta_x))
        
        return angle
    
    def analyze_eyes(self, face_landmarks, image_shape: Tuple[int, int, int]) -> Dict:
        """
        Analyze eye visibility and state.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            image_shape: Shape of the image
            
        Returns:
            Dictionary with eye analysis results
        """
        height, width = image_shape[:2]
        
        # Eye landmark indices (MediaPipe 468 landmark model)
        # Left eye: 33, 133, 160, 159, 158, 157, 173
        # Right eye: 362, 263, 387, 386, 385, 384, 398
        
        left_eye_landmarks = [33, 133, 160, 159, 158, 157, 173]
        right_eye_landmarks = [362, 263, 387, 386, 385, 384, 398]
        
        # Calculate Eye Aspect Ratio (EAR) to detect closed eyes
        left_ear = self._calculate_eye_aspect_ratio(face_landmarks, left_eye_landmarks, image_shape)
        right_ear = self._calculate_eye_aspect_ratio(face_landmarks, right_eye_landmarks, image_shape)
        
        # Eyes are considered closed if EAR < 0.2
        eyes_closed = left_ear < 0.2 or right_ear < 0.2
        
        return {
            "both_eyes_visible": True,  # If landmarks detected, eyes are visible
            "eyes_closed": eyes_closed,
            "left_eye_aspect_ratio": left_ear,
            "right_eye_aspect_ratio": right_ear
        }
    
    def _calculate_eye_aspect_ratio(self, face_landmarks, eye_indices: List[int], 
                                    image_shape: Tuple[int, int, int]) -> float:
        """Calculate Eye Aspect Ratio (EAR) for eye openness detection"""
        height, width = image_shape[:2]
        
        # Get eye landmarks
        points = []
        for idx in eye_indices:
            landmark = face_landmarks.landmark[idx]
            points.append([landmark.x * width, landmark.y * height])
        
        points = np.array(points)
        
        # Calculate vertical distances
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        
        # Calculate horizontal distance
        C = np.linalg.norm(points[0] - points[3])
        
        # Eye Aspect Ratio
        ear = (A + B) / (2.0 * C)
        
        return ear
    
    def analyze_gaze_direction(self, face_landmarks, image_shape: Tuple[int, int, int]) -> Dict:
        """
        Analyze gaze direction.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            image_shape: Shape of the image
            
        Returns:
            Dictionary with gaze analysis
        """
        # Simplified gaze detection based on iris position
        # For production, consider using MediaPipe Iris model
        
        # Check if face is roughly frontal by comparing nose position
        # Nose tip: landmark 1
        # Left face edge: landmark 234
        # Right face edge: landmark 454
        
        nose = face_landmarks.landmark[1]
        left_edge = face_landmarks.landmark[234]
        right_edge = face_landmarks.landmark[454]
        
        # If nose is roughly centered between face edges, looking at camera
        nose_x = nose.x
        left_x = left_edge.x
        right_x = right_edge.x
        
        face_center = (left_x + right_x) / 2
        offset = abs(nose_x - face_center)
        
        # If offset is less than 5% of face width, looking at camera
        looking_at_camera = offset < 0.05
        
        return {
            "looking_at_camera": looking_at_camera,
            "horizontal_offset": offset
        }
    
    def check_mouth_open(self, face_landmarks, image_shape: Tuple[int, int, int]) -> bool:
        """
        Check if mouth is open.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            image_shape: Shape of the image
            
        Returns:
            True if mouth is open, False otherwise
        """
        height, width = image_shape[:2]
        
        # Upper lip: landmark 13
        # Lower lip: landmark 14
        upper_lip = face_landmarks.landmark[13]
        lower_lip = face_landmarks.landmark[14]
        
        # Calculate vertical distance
        distance = abs(upper_lip.y - lower_lip.y) * height
        
        # Mouth is considered open if distance > 10 pixels
        mouth_open = distance > 10
        
        return mouth_open
    
    def detect_glasses(self, image: np.ndarray, face_landmarks) -> bool:
        """
        Detect if person is wearing glasses.
        
        Args:
            image: Image as numpy array
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            True if glasses detected, False otherwise
        """
        # Simple glasses detection using edge detection around eye regions
        # For production, consider training a dedicated classifier
        
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Get eye regions
        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        
        # Create regions around eyes
        left_x = int(left_eye.x * width)
        left_y = int(left_eye.y * height)
        right_x = int(right_eye.x * width)
        right_y = int(right_eye.y * height)
        
        # Extract eye regions (with padding)
        padding = 30
        left_region = gray[max(0, left_y-padding):min(height, left_y+padding),
                          max(0, left_x-padding):min(width, left_x+padding)]
        right_region = gray[max(0, right_y-padding):min(height, right_y+padding),
                           max(0, right_x-padding):min(width, right_x+padding)]
        
        # Apply edge detection
        left_edges = cv2.Canny(left_region, 50, 150)
        right_edges = cv2.Canny(right_region, 50, 150)
        
        # Count edge pixels (glasses frames create strong edges)
        left_edge_count = np.sum(left_edges > 0)
        right_edge_count = np.sum(right_edges > 0)
        
        # If high edge density, likely glasses
        # This is a simplified heuristic
        total_edges = left_edge_count + right_edge_count
        glasses_threshold = 200  # Adjust based on testing
        
        return total_edges > glasses_threshold


# Create global instance
face_detection_service = FaceDetectionService()
