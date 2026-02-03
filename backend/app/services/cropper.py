import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, Optional, List


class SubjectDetector:
    """Service for detecting subjects in video frames using MediaPipe."""
    
    def __init__(self):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Full range model (better for videos)
            min_detection_confidence=0.5
        )
        
        # Initialize MediaPipe Pose Detection as fallback
        self.mp_pose = mp.solutions.pose
        self.pose_detection = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5
        )
    
    def detect_subject_center(self, frame: np.ndarray) -> Optional[Tuple[int, int]]:
        """
        Detect the center of the main subject in a frame.
        
        Args:
            frame: BGR image from OpenCV
            
        Returns:
            (x, y) center coordinates or None if no subject found
        """
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Try face detection first
        face_results = self.face_detection.process(rgb_frame)
        if face_results.detections:
            # Use the first (most confident) detection
            detection = face_results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            # Calculate center of face
            center_x = int((bbox.xmin + bbox.width / 2) * w)
            center_y = int((bbox.ymin + bbox.height / 2) * h)
            return (center_x, center_y)
        
        # Try pose detection as fallback
        pose_results = self.pose_detection.process(rgb_frame)
        if pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            
            # Calculate average position of key landmarks (shoulders, nose)
            key_indices = [0, 11, 12]  # Nose, left shoulder, right shoulder
            x_sum, y_sum, count = 0, 0, 0
            
            for idx in key_indices:
                if landmarks[idx].visibility > 0.5:
                    x_sum += landmarks[idx].x * w
                    y_sum += landmarks[idx].y * h
                    count += 1
            
            if count > 0:
                return (int(x_sum / count), int(y_sum / count))
        
        return None
    
    def analyze_clip(
        self, 
        video_path: str, 
        sample_frames: int = 10
    ) -> Tuple[int, int]:
        """
        Analyze a video clip and determine the average subject center.
        
        Args:
            video_path: Path to the video clip
            sample_frames: Number of frames to sample
            
        Returns:
            (x, y) average center coordinates, or video center if no subject found
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Sample frames evenly
        sample_indices = np.linspace(0, frame_count - 1, sample_frames, dtype=int)
        
        centers: List[Tuple[int, int]] = []
        
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            center = self.detect_subject_center(frame)
            if center:
                centers.append(center)
        
        cap.release()
        
        if centers:
            # Calculate average center
            avg_x = int(np.mean([c[0] for c in centers]))
            avg_y = int(np.mean([c[1] for c in centers]))
            return (avg_x, avg_y)
        
        # Fallback to video center
        return (width // 2, height // 2)
    
    def calculate_crop_region(
        self,
        frame_width: int,
        frame_height: int,
        subject_center: Tuple[int, int],
        target_width: int = 720,
        target_height: int = 1280
    ) -> Tuple[int, int, int, int]:
        """
        Calculate the crop region for 9:16 output centered on subject.
        
        Args:
            frame_width: Original frame width
            frame_height: Original frame height
            subject_center: (x, y) center of the subject
            target_width: Output width (720)
            target_height: Output height (1280)
            
        Returns:
            (x, y, width, height) crop region
        """
        target_aspect = target_width / target_height  # 0.5625 for 9:16
        
        # Calculate crop dimensions maintaining aspect ratio
        # We want to maximize the crop size while maintaining aspect ratio
        if frame_height * target_aspect <= frame_width:
            # Height-limited: use full height
            crop_height = frame_height
            crop_width = int(frame_height * target_aspect)
        else:
            # Width-limited: use full width
            crop_width = frame_width
            crop_height = int(frame_width / target_aspect)
        
        # Calculate crop position centered on subject
        center_x, center_y = subject_center
        
        # Calculate crop origin
        crop_x = center_x - crop_width // 2
        crop_y = center_y - crop_height // 2
        
        # Clamp to frame boundaries
        crop_x = max(0, min(crop_x, frame_width - crop_width))
        crop_y = max(0, min(crop_y, frame_height - crop_height))
        
        return (crop_x, crop_y, crop_width, crop_height)
    
    def close(self):
        """Release MediaPipe resources."""
        self.face_detection.close()
        self.pose_detection.close()
