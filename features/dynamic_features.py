"""
Sprint 3 - Dynamic Feature Extraction Module
==============================================
Temporal Stroke Signal Processing & Behavioral Feature Extraction

Module: dynamic_features.py
Author: Jesun - Dynamic Feature Generation Lead
Date: February 16-March 2, 2026

Purpose:
Extract temporal/dynamic features from drawing session data.
Dynamic features = features derived from live interaction timing and movement patterns.

Key Features:
- Temporal signal validation and continuity checking
- Real-time behavioral signal extraction
- Speed/velocity profile calculation
- Acceleration pattern analysis
- Stroke timing statistics
- Pause detection and analysis
- Movement rhythm extraction
- Direction changes and curvature calculation

Classes:
--------
- DrawingSessionValidator: Validates temporal data integrity
- DynamicFeatureExtractor: Extracts all dynamic features
- StrokeAnalyzer: Low-level stroke analysis

Functions:
----------
See individual class methods for comprehensive documentation.
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import warnings


def parse_timestamp(timestamp) -> datetime:
    """
    Parse timestamp from either Unix timestamp (int/float in milliseconds) or ISO string.
    
    Args:
        timestamp: Either int/float (Unix ms) or ISO string
        
    Returns:
        datetime object
    """
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp / 1000)
    else:
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


@dataclass
class TemporalValidationResult:
    """Result of temporal validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


@dataclass
class DynamicFeatures:
    """Container for extracted dynamic features"""
    # Speed features
    avg_speed: float
    max_speed: float
    min_speed: float
    speed_variance: float
    speed_profile: List[float]
    
    # Acceleration features
    avg_acceleration: float
    max_acceleration: float
    acceleration_variance: float
    acceleration_profile: List[float]
    
    # Stroke timing
    total_drawing_time: float  # milliseconds
    total_pause_time: float    # milliseconds
    stroke_durations: List[float]  # milliseconds per stroke
    
    # Pause analysis
    number_of_pauses: int
    avg_pause_duration: float
    max_pause_duration: float
    pause_durations: List[float]
    
    # Movement rhythm
    inter_stroke_interval: List[float]  # time between strokes
    avg_inter_stroke_interval: float
    stroke_frequency: float  # strokes per second
    
    # Direction & curvature
    direction_changes: int
    avg_curvature: float
    max_curvature: float
    curvature_profile: List[float]
    
    # Overall statistics
    total_strokes: int
    total_points: int
    avg_points_per_stroke: float
    drawing_area: float  # bounding box area


class DrawingSessionValidator:
    """
    Validates temporal integrity of drawing sessions.
    
    Ensures:
    - Timestamps are monotonically increasing within strokes
    - Time values are reasonable (not negative, not in future)
    - All required fields present
    - No data corruption
    """
    
    @staticmethod
    def validate_session(session: Dict) -> TemporalValidationResult:
        """
        Validate temporal integrity of entire session.
        
        Args:
            session: Drawing session JSON object
            
        Returns:
            TemporalValidationResult with validation status and details
        """
        errors = []
        warnings = []
        stats = {}
        
        try:
            # Check required top-level fields
            required_fields = ['sessionId', 'sessionStartTime', 'strokes', 'deviceInfo']
            for field in required_fields:
                if field not in session:
                    errors.append(f"Missing required field: {field}")
            
            if errors:
                return TemporalValidationResult(False, errors, warnings, {})
            
            # Validate session timestamps
            task_start = parse_timestamp(session['sessionStartTime'])
            task_end = parse_timestamp(session.get('sessionEndTime', session['sessionStartTime']))
            
            if task_end < task_start:
                errors.append("Task end time is before start time")
            
            session_duration_ms = (task_end - task_start).total_seconds() * 1000
            stats['session_duration_ms'] = session_duration_ms
            
            # Validate each stroke
            total_points = 0
            stroke_count = len(session['strokes'])
            
            for idx, stroke in enumerate(session['strokes']):
                stroke_errors = DrawingSessionValidator.validate_stroke(stroke, idx)
                errors.extend(stroke_errors)
                total_points += len(stroke.get('points', []))
            
            stats['total_strokes'] = stroke_count
            stats['total_points'] = total_points
            stats['avg_points_per_stroke'] = total_points / max(stroke_count, 1)
            
            is_valid = len(errors) == 0
            
            return TemporalValidationResult(is_valid, errors, warnings, stats)
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return TemporalValidationResult(False, errors, warnings, stats)
    
    @staticmethod
    def validate_stroke(stroke: Dict, stroke_idx: int) -> List[str]:
        """
        Validate temporal integrity of single stroke.
        
        Args:
            stroke: Stroke object
            stroke_idx: Index of stroke in session
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check required stroke fields
            required = ['strokeId', 'points', 'startTime', 'endTime']
            for field in required:
                if field not in stroke:
                    errors.append(f"Stroke {stroke_idx}: Missing {field}")
                    return errors  # Can't continue without critical fields
            
            points = stroke['points']
            if not points:
                errors.append(f"Stroke {stroke_idx}: No points")
                return errors
            
            # Validate point timestamps are monotonically increasing
            prev_timestamp = None
            for pt_idx, point in enumerate(points):
                if 'timestamp' not in point:
                    errors.append(f"Stroke {stroke_idx}, Point {pt_idx}: Missing timestamp")
                    continue
                
                timestamp = point['timestamp']
                
                # Check timestamp is positive
                if timestamp < 0:
                    errors.append(f"Stroke {stroke_idx}, Point {pt_idx}: Negative timestamp")
                
                # Check monotonic increasing
                if prev_timestamp is not None and timestamp < prev_timestamp:
                    errors.append(f"Stroke {stroke_idx}, Point {pt_idx}: Timestamp not monotonically increasing")
                
                prev_timestamp = timestamp
            
            # Validate stroke start/end times
            stroke_start = parse_timestamp(stroke['startTime'])
            stroke_end = parse_timestamp(stroke['endTime'])
            
            if stroke_end < stroke_start:
                errors.append(f"Stroke {stroke_idx}: End time before start time")
            
        except Exception as e:
            errors.append(f"Stroke {stroke_idx}: {str(e)}")
        
        return errors


class StrokeAnalyzer:
    """
    Low-level analysis of individual strokes.
    Calculates point-level and stroke-level metrics.
    """
    
    @staticmethod
    def calculate_distances(stroke: Dict) -> np.ndarray:
        """
        Calculate Euclidean distances between consecutive points.
        
        Args:
            stroke: Stroke object with points
            
        Returns:
            Array of distances (pixels)
        """
        points = stroke['points']
        if len(points) < 2:
            return np.array([])
        
        coords = np.array([[p['x'], p['y']] for p in points])
        distances = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1))
        return distances
    
    @staticmethod
    def calculate_time_deltas(stroke: Dict) -> np.ndarray:
        """
        Calculate time differences between consecutive points.
        
        Args:
            stroke: Stroke object with points
            
        Returns:
            Array of time deltas (milliseconds)
        """
        points = stroke['points']
        if len(points) < 2:
            return np.array([])
        
        timestamps = np.array([p['timestamp'] for p in points])
        time_deltas = np.diff(timestamps)
        return time_deltas
    
    @staticmethod
    def calculate_velocity(stroke: Dict) -> Tuple[np.ndarray, float, float, float]:
        """
        Calculate velocity (pixels/millisecond) for each segment.
        
        Args:
            stroke: Stroke object
            
        Returns:
            Tuple of (velocity_array, avg_velocity, max_velocity, min_velocity)
        """
        distances = StrokeAnalyzer.calculate_distances(stroke)
        time_deltas = StrokeAnalyzer.calculate_time_deltas(stroke)
        
        if len(time_deltas) == 0 or np.any(time_deltas == 0):
            return np.array([]), 0, 0, 0
        
        # Avoid division by zero
        velocities = np.divide(distances, time_deltas, 
                              where=time_deltas != 0,
                              out=np.zeros_like(distances, dtype=float))
        
        avg_vel = np.mean(velocities) if len(velocities) > 0 else 0
        max_vel = np.max(velocities) if len(velocities) > 0 else 0
        min_vel = np.min(velocities) if len(velocities) > 0 else 0
        
        return velocities, avg_vel, max_vel, min_vel
    
    @staticmethod
    def calculate_acceleration(stroke: Dict) -> Tuple[np.ndarray, float, float]:
        """
        Calculate acceleration (change in velocity).
        
        Args:
            stroke: Stroke object
            
        Returns:
            Tuple of (acceleration_array, avg_acceleration, max_acceleration)
        """
        velocities, _, _, _ = StrokeAnalyzer.calculate_velocity(stroke)
        time_deltas = StrokeAnalyzer.calculate_time_deltas(stroke)
        
        if len(velocities) < 2 or np.any(time_deltas == 0):
            return np.array([]), 0, 0
        
        # Acceleration = change in velocity / time
        accel = np.diff(velocities) / time_deltas[:-1]
        avg_accel = np.mean(np.abs(accel)) if len(accel) > 0 else 0
        max_accel = np.max(np.abs(accel)) if len(accel) > 0 else 0
        
        return accel, avg_accel, max_accel
    
    @staticmethod
    def calculate_curvature(stroke: Dict) -> Tuple[List[float], float, float]:
        """
        Calculate curvature at each point (rate of direction change).
        
        Curvature = |dθ/ds| where θ is angle and s is arc length
        
        Args:
            stroke: Stroke object
            
        Returns:
            Tuple of (curvature_profile, avg_curvature, max_curvature)
        """
        points = stroke['points']
        if len(points) < 3:
            return [], 0, 0
        
        coords = np.array([[p['x'], p['y']] for p in points])
        
        # Calculate vectors between consecutive points
        vectors = np.diff(coords, axis=0)
        
        curvatures = []
        for i in range(len(vectors) - 1):
            v1 = vectors[i]
            v2 = vectors[i + 1]
            
            # Normalize vectors
            v1_norm = np.linalg.norm(v1)
            v2_norm = np.linalg.norm(v2)
            
            if v1_norm == 0 or v2_norm == 0:
                curvatures.append(0)
                continue
            
            # Calculate angle between vectors
            cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
            cos_angle = np.clip(cos_angle, -1, 1)  # Handle numerical errors
            angle = np.arccos(cos_angle)
            
            # Curvature ~ angle / distance
            distance = (v1_norm + v2_norm) / 2
            curvature = angle / distance if distance > 0 else 0
            curvatures.append(curvature)
        
        curvatures = np.array(curvatures)
        avg_curv = np.mean(curvatures) if len(curvatures) > 0 else 0
        max_curv = np.max(curvatures) if len(curvatures) > 0 else 0
        
        return curvatures.tolist(), avg_curv, max_curv
    
    @staticmethod
    def count_direction_changes(stroke: Dict, angle_threshold: float = 30) -> int:
        """
        Count number of significant direction changes in stroke.
        
        Args:
            stroke: Stroke object
            angle_threshold: Minimum angle (degrees) to count as direction change
            
        Returns:
            Count of direction changes
        """
        points = stroke['points']
        if len(points) < 3:
            return 0
        
        coords = np.array([[p['x'], p['y']] for p in points])
        vectors = np.diff(coords, axis=0)
        
        direction_changes = 0
        for i in range(len(vectors) - 1):
            v1 = vectors[i]
            v2 = vectors[i + 1]
            
            v1_norm = np.linalg.norm(v1)
            v2_norm = np.linalg.norm(v2)
            
            if v1_norm == 0 or v2_norm == 0:
                continue
            
            cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
            cos_angle = np.clip(cos_angle, -1, 1)
            angle_rad = np.arccos(cos_angle)
            angle_deg = np.degrees(angle_rad)
            
            if angle_deg > angle_threshold:
                direction_changes += 1
        
        return direction_changes


class DynamicFeatureExtractor:
    """
    Extract all dynamic (temporal) features from drawing session.
    
    Main interface for feature extraction.
    Coordinates all sub-analyzers and compiles final feature set.
    """
    
    def __init__(self, session: Dict, validate: bool = True):
        """
        Initialize feature extractor.
        
        Args:
            session: Drawing session JSON object
            validate: Whether to validate temporal integrity
        """
        self.session = session
        self.validate = validate
        self._validation_result = None
        
        if validate:
            self._validation_result = DrawingSessionValidator.validate_session(session)
    
    def extract_all_features(self) -> DynamicFeatures:
        """
        Extract complete set of dynamic features.
        
        Returns:
            DynamicFeatures object with all calculated metrics
        """
        if self.validate and not self._validation_result.is_valid:
            warnings.warn(f"Session validation failed: {self._validation_result.errors}")
        
        strokes = self.session.get('strokes', [])
        
        # Initialize feature lists
        all_speeds = []
        all_accelerations = []
        all_curvatures = []
        all_stroke_durations = []
        all_pause_durations = []
        inter_stroke_intervals = []
        
        # Analyze each stroke
        for idx, stroke in enumerate(strokes):
            # Speed analysis
            vel_profile, avg_vel, max_vel, min_vel = StrokeAnalyzer.calculate_velocity(stroke)
            all_speeds.extend(vel_profile.tolist())
            
            # Acceleration analysis
            accel_profile, avg_accel, max_accel = StrokeAnalyzer.calculate_acceleration(stroke)
            all_accelerations.extend(accel_profile.tolist())
            
            # Curvature analysis
            curv_profile, avg_curv, max_curv = StrokeAnalyzer.calculate_curvature(stroke)
            all_curvatures.extend(curv_profile)
            
            # Stroke duration
            stroke_start = parse_timestamp(stroke['startTime'])
            stroke_end = parse_timestamp(stroke['endTime'])
            stroke_duration = (stroke_end - stroke_start).total_seconds() * 1000
            all_stroke_durations.append(stroke_duration)
        
        # Post-stroke pause analysis
        for idx in range(len(strokes) - 1):
            stroke_end = parse_timestamp(strokes[idx]['endTime'])
            next_stroke_start = parse_timestamp(strokes[idx + 1]['startTime'])
            pause_duration = (next_stroke_start - stroke_end).total_seconds() * 1000
            
            if pause_duration > 0:
                all_pause_durations.append(pause_duration)
                inter_stroke_intervals.append(pause_duration)
        
        # Calculate aggregate statistics
        speed_array = np.array(all_speeds)
        accel_array = np.array(all_accelerations)
        curv_array = np.array(all_curvatures)
        
        # Count direction changes
        total_direction_changes = sum(
            StrokeAnalyzer.count_direction_changes(stroke) 
            for stroke in strokes
        )
        
        # Drawing bounding box
        all_x = []
        all_y = []
        for stroke in strokes:
            for point in stroke.get('points', []):
                all_x.append(point.get('x', 0))
                all_y.append(point.get('y', 0))
        
        drawing_area = 0
        if all_x and all_y:
            width = max(all_x) - min(all_x)
            height = max(all_y) - min(all_y)
            drawing_area = width * height
        
        # Session timing
        task_start = parse_timestamp(self.session['sessionStartTime'])
        task_end = parse_timestamp(self.session.get('sessionEndTime', self.session['sessionStartTime']))
        total_session_time = (task_end - task_start).total_seconds() * 1000
        
        total_drawing_time = sum(all_stroke_durations)
        total_pause_time = sum(all_pause_durations)
        
        # Create features object
        features = DynamicFeatures(
            # Speed
            avg_speed=float(np.mean(speed_array)) if len(speed_array) > 0 else 0,
            max_speed=float(np.max(speed_array)) if len(speed_array) > 0 else 0,
            min_speed=float(np.min(speed_array)) if len(speed_array) > 0 else 0,
            speed_variance=float(np.var(speed_array)) if len(speed_array) > 0 else 0,
            speed_profile=speed_array.tolist(),
            
            # Acceleration
            avg_acceleration=float(np.mean(np.abs(accel_array))) if len(accel_array) > 0 else 0,
            max_acceleration=float(np.max(np.abs(accel_array))) if len(accel_array) > 0 else 0,
            acceleration_variance=float(np.var(accel_array)) if len(accel_array) > 0 else 0,
            acceleration_profile=accel_array.tolist(),
            
            # Timing
            total_drawing_time=total_drawing_time,
            total_pause_time=total_pause_time,
            stroke_durations=all_stroke_durations,
            
            # Pauses
            number_of_pauses=len(all_pause_durations),
            avg_pause_duration=float(np.mean(all_pause_durations)) if all_pause_durations else 0,
            max_pause_duration=float(np.max(all_pause_durations)) if all_pause_durations else 0,
            pause_durations=all_pause_durations,
            
            # Rhythm
            inter_stroke_interval=inter_stroke_intervals,
            avg_inter_stroke_interval=float(np.mean(inter_stroke_intervals)) if inter_stroke_intervals else 0,
            stroke_frequency=len(strokes) / (total_session_time / 1000) if total_session_time > 0 else 0,
            
            # Direction & curvature
            direction_changes=total_direction_changes,
            avg_curvature=float(np.mean(curv_array)) if len(curv_array) > 0 else 0,
            max_curvature=float(np.max(curv_array)) if len(curv_array) > 0 else 0,
            curvature_profile=curv_array.tolist(),
            
            # Overall
            total_strokes=len(strokes),
            total_points=sum(len(stroke.get('points', [])) for stroke in strokes),
            avg_points_per_stroke=sum(len(stroke.get('points', [])) for stroke in strokes) / max(len(strokes), 1),
            drawing_area=drawing_area
        )
        
        return features
    
    def get_validation_report(self) -> Dict:
        """Get detailed validation report."""
        if not self._validation_result:
            return {"status": "Not validated"}
        
        return {
            "is_valid": self._validation_result.is_valid,
            "errors": self._validation_result.errors,
            "warnings": self._validation_result.warnings,
            "stats": self._validation_result.stats
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert features to pandas DataFrame (single row).
        
        Returns:
            DataFrame with one row containing all features
        """
        features = self.extract_all_features()
        features_dict = asdict(features)
        
        # Expand list fields into separate columns or keep as JSON
        # For now, convert lists to JSON strings for DataFrame compatibility
        for key, value in features_dict.items():
            if isinstance(value, list):
                features_dict[key] = json.dumps(value)
        
        return pd.DataFrame([features_dict])


def load_and_extract_features(session_path: str) -> Tuple[DynamicFeatures, Dict]:
    """
    Load session from file and extract features.
    
    Args:
        session_path: Path to session JSON file
        
    Returns:
        Tuple of (DynamicFeatures, validation_report)
    """
    with open(session_path, 'r') as f:
        session = json.load(f)
    
    extractor = DynamicFeatureExtractor(session, validate=True)
    features = extractor.extract_all_features()
    validation = extractor.get_validation_report()
    
    return features, validation


if __name__ == "__main__":
    # Example usage
    print("Dynamic Feature Extraction Module")
    print("=" * 50)
    print("\nExample: Load and extract features from session JSON")
    print("\nUsage:")
    print("-" * 50)
    print("""
from dynamic_feature_extraction import DynamicFeatureExtractor
import json

# Load session
with open('session.json') as f:
    session = json.load(f)

# Extract features
extractor = DynamicFeatureExtractor(session, validate=True)
features = extractor.extract_all_features()

# Get validation report
print(extractor.get_validation_report())

# Convert to DataFrame
df = extractor.to_dataframe()
print(df)

# Access specific features
print(f"Average speed: {features.avg_speed}")
print(f"Total drawing time: {features.total_drawing_time} ms")
    """)
