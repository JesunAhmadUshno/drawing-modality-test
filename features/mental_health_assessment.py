"""
Mental Health Assessment Module
Predicts User Psychological State (Stress, Anxiety, Burnout, Cognitive Load)
Based on Drawing Dynamics and Behavioral Metrics

Scientific Basis:
- Psychomotor analysis research (handwriting dynamics correlate with psychological states)
- Stress detection through keystroke/drawing dynamics
- Cognitive load assessment through motor control analysis
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MentalHealthProfile:
    """Comprehensive mental health assessment result."""
    stress_score: float  # 0-100 (higher = more stressed)
    anxiety_score: float  # 0-100 (higher = more anxious)
    burnout_score: float  # 0-100 (higher = more burned out)
    cognitive_load_score: float  # 0-100 (higher = more overloaded)
    overall_wellness: float  # 0-100 (higher = better)
    
    # Recommendations
    primary_concern: str
    recommendations: List[str]
    trend: str  # "improving", "stable", "declining"
    
    # Detailed breakdown
    indicators: Dict[str, float]


class MentalHealthAssessmentEngine:
    """
    Analyzes drawing metrics to assess mental health state.
    Uses evidence-based indicators from psychological research.
    """
    
    def __init__(self):
        # Thresholds (can be calibrated)
        self.thresholds = {
            'tremor_high': 0.7,  # High variability in strokes
            'pause_freq_high': 0.6,  # Frequent hesitations
            'efficiency_low': 30,  # Low drawing efficiency
            'speed_inconsistent': 0.75,  # High variation in speed
            'quality_declining': 0.7,  # Quality dropping over time
            'pressure_unstable': 0.65  # Pressure changes
        }
    
    def assess(self, session_data: Dict, historical_sessions: List[Dict] = None) -> MentalHealthProfile:
        """
        Perform comprehensive mental health assessment.
        
        Args:
            session_data: Current session metrics
            historical_sessions: Previous sessions for trend analysis
            
        Returns:
            MentalHealthProfile with detailed assessment
        """
        # Extract indicators
        indicators = self._extract_indicators(session_data)
        
        # Calculate dimension scores
        stress_score = self._calculate_stress(indicators, session_data)
        anxiety_score = self._calculate_anxiety(indicators, session_data)
        burnout_score = self._calculate_burnout(indicators, session_data, historical_sessions)
        cognitive_load = self._calculate_cognitive_load(indicators, session_data)
        
        # Overall wellness (inverse of negative indicators)
        overall_wellness = 100 - np.mean([stress_score, anxiety_score, burnout_score, cognitive_load])
        
        # Trend analysis
        trend = self._analyze_trend(historical_sessions) if historical_sessions else "stable"
        
        # Primary concern
        scores = {
            'stress': stress_score,
            'anxiety': anxiety_score,
            'burnout': burnout_score,
            'cognitive_load': cognitive_load
        }
        primary_concern = max(scores, key=scores.get)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            stress_score, anxiety_score, burnout_score, cognitive_load
        )
        
        return MentalHealthProfile(
            stress_score=round(stress_score, 1),
            anxiety_score=round(anxiety_score, 1),
            burnout_score=round(burnout_score, 1),
            cognitive_load_score=round(cognitive_load, 1),
            overall_wellness=round(overall_wellness, 1),
            primary_concern=primary_concern,
            recommendations=recommendations,
            trend=trend,
            indicators=indicators
        )
    
    def _extract_indicators(self, session_data: Dict) -> Dict[str, float]:
        """Extract psychological indicators from metrics."""
        indicators = {}
        
        # 1. TREMOR/JITTER (Indicator of Stress/Anxiety)
        # Higher variability in stroke acceleration = more tremor
        dynamic = session_data.get('features', {}).get('dynamic', {})
        temporal = dynamic.get('temporal', {})
        
        if 'acceleration_profile' in temporal:
            accel = temporal['acceleration_profile']
            if isinstance(accel, list) and len(accel) > 0:
                indicators['tremor_index'] = float(np.std(accel)) / (np.mean(np.abs(accel)) + 1e-5)
            else:
                indicators['tremor_index'] = 0.0
        else:
            indicators['tremor_index'] = 0.0
        
        # 2. PAUSE FREQUENCY (Hesitation indicator - Anxiety/Stress)
        timing = dynamic.get('timing', {})
        total_pause_ms = timing.get('total_pause_time_ms', 0)
        total_drawing_ms = timing.get('total_drawing_time_ms', 1)
        indicators['pause_ratio'] = total_pause_ms / (total_pause_ms + total_drawing_ms)
        
        # Count pauses (from pause_events)
        pause_events = timing.get('pause_events', 0)
        total_strokes = timing.get('strokes', 1)
        indicators['pause_frequency'] = min(pause_events / max(total_strokes, 1), 1.0)
        
        # 3. SPEED CONSISTENCY (High variation = Anxiety/Stress)
        motion = dynamic.get('motion', {})
        if 'avg_speed_per_stroke' in motion:
            speeds = motion['avg_speed_per_stroke']
            if isinstance(speeds, list) and len(speeds) > 0:
                # Coefficient of variation
                indicators['speed_inconsistency'] = float(np.std(speeds)) / (np.mean(speeds) + 1e-5)
            else:
                indicators['speed_inconsistency'] = 0.0
        else:
            indicators['speed_inconsistency'] = 0.0
        
        # 4. DRAWING EFFICIENCY (Low efficiency = Burnout/Fatigue)
        assessment = session_data.get('analysis', {}).get('assessment', {})
        indicators['efficiency_level'] = assessment.get('drawing_efficiency', 50)
        
        # 5. SHAPE QUALITY (Declining quality = Burnout)
        indicators['quality_level'] = assessment.get('shape_quality', 50)
        
        # 6. PRESSURE STABILITY (Variable pressure = Anxiety)
        # Calculate from stroke data if available
        indicators['pressure_stability'] = self._calculate_pressure_stability(session_data)
        
        # 7. MOVEMENT FLUIDITY (Smooth vs jerky = Stress)
        rhythm = dynamic.get('rhythm', {})
        indicators['fluidity_index'] = rhythm.get('rhythm_regularity', 0.5)
        
        # 8. SESSION DURATION (Unusually long = Stress/Burnout/Cognitive Overload)
        session_duration_s = (total_pause_ms + total_drawing_ms) / 1000
        # Normalize: assume normal = 60-90s
        if session_duration_s > 120:
            indicators['duration_concern'] = min((session_duration_s - 120) / 120, 1.0)
        elif session_duration_s < 30:
            indicators['duration_concern'] = min((30 - session_duration_s) / 30, 1.0)
        else:
            indicators['duration_concern'] = 0.0
        
        # 9. COMPLETION RATE (Low completion = Burnout/Cognitive Overload)
        summary = session_data.get('summary', {})
        is_complete = summary.get('is_complete', False)
        indicators['completion_status'] = 1.0 if is_complete else 0.5
        
        # 10. ERROR COUNT (High errors = Stress/Cognitive Overload)
        total_errors = summary.get('total_errors', 0)
        indicators['error_count'] = min(total_errors / 5, 1.0)  # Normalize
        
        return indicators
    
    def _calculate_pressure_stability(self, session_data: Dict) -> float:
        """Calculate stability of pressure during drawing."""
        # Try to extract pressure data from strokes
        try:
            raw_data = session_data.get('raw_session_data', {})
            tasks = raw_data.get('tasks', [])
            
            pressures = []
            for task in tasks:
                strokes = task.get('strokes', [])
                for stroke in strokes:
                    points = stroke.get('points', [])
                    for point in points:
                        if 'pressure' in point:
                            pressures.append(point['pressure'])
            
            if len(pressures) > 5:
                # Higher = more stable
                stability = 1.0 - (np.std(pressures) / (np.mean(pressures) + 1e-5))
                return max(0, min(stability, 1.0))
        except:
            pass
        
        return 0.5  # Default neutral
    
    def _calculate_stress(self, indicators: Dict, session_data: Dict) -> float:
        """
        Calculate stress score (0-100).
        
        Stress indicators:
        - High tremor/jitter
        - Speed inconsistency
        - Frequent pauses
        - Pressure instability
        """
        stress = 0.0
        weights = {}
        
        # Tremor (40% weight)
        stress += min(indicators['tremor_index'] * 100, 100) * 0.4
        weights['tremor'] = min(indicators['tremor_index'] * 100, 100)
        
        # Speed inconsistency (30% weight)
        stress += min(indicators['speed_inconsistency'] * 100, 100) * 0.3
        weights['speed_var'] = min(indicators['speed_inconsistency'] * 100, 100)
        
        # Pause frequency (20% weight)
        stress += indicators['pause_frequency'] * 100 * 0.2
        weights['pause_freq'] = indicators['pause_frequency'] * 100
        
        # Pressure instability (10% weight)
        stress += (1.0 - indicators['pressure_stability']) * 100 * 0.1
        weights['pressure'] = (1.0 - indicators['pressure_stability']) * 100
        
        return min(stress, 100)
    
    def _calculate_anxiety(self, indicators: Dict, session_data: Dict) -> float:
        """
        Calculate anxiety score (0-100).
        
        Anxiety indicators:
        - Tremor/jitter
        - Hesitation (pauses)
        - Speed inconsistency
        - Pressure variability
        - Low fluidity
        """
        anxiety = 0.0
        
        # These overlap with stress but different weighting
        # Tremor (25% weight)
        anxiety += min(indicators['tremor_index'] * 100, 100) * 0.25
        
        # Pause frequency - hesitation (30% weight)
        anxiety += indicators['pause_frequency'] * 100 * 0.3
        
        # Speed inconsistency (20% weight)
        anxiety += min(indicators['speed_inconsistency'] * 100, 100) * 0.2
        
        # Low fluidity (15% weight)
        anxiety += (1.0 - indicators['fluidity_index']) * 100 * 0.15
        
        # Pressure stability (10% weight)
        anxiety += (1.0 - indicators['pressure_stability']) * 100 * 0.1
        
        return min(anxiety, 100)
    
    def _calculate_burnout(self, indicators: Dict, session_data: Dict, 
                          historical_sessions: List[Dict] = None) -> float:
        """
        Calculate burnout score (0-100).
        
        Burnout indicators:
        - Low drawing efficiency (can't focus)
        - Declining quality over time
        - More errors
        - Longer session duration
        - Incomplete tasks
        """
        burnout = 0.0
        
        # Low efficiency (35% weight)
        burnout += (100 - indicators['efficiency_level']) * 0.35
        
        # Low quality (25% weight)
        burnout += (100 - indicators['quality_level']) * 0.25
        
        # Incomplete tasks (20% weight)
        burnout += (1.0 - indicators['completion_status']) * 100 * 0.2
        
        # Duration concern (15% weight)
        burnout += indicators['duration_concern'] * 100 * 0.15
        
        # Trend analysis (5% weight) - declining = more burnout
        if historical_sessions and len(historical_sessions) > 2:
            # If last 3 sessions show declining efficiency, increase burnout
            recent_eff = [s.get('analysis', {}).get('assessment', {}).get('drawing_efficiency', 50) 
                         for s in historical_sessions[-3:]]
            if len(recent_eff) >= 2:
                trend_decline = recent_eff[0] - recent_eff[-1]
                if trend_decline > 15:  # Significant decline
                    burnout += 15 * 0.05
        
        return min(burnout, 100)
    
    def _calculate_cognitive_load(self, indicators: Dict, session_data: Dict) -> float:
        """
        Calculate cognitive load score (0-100).
        
        Cognitive overload indicators:
        - Speed inconsistency (can't plan strokes)
        - High error rate
        - Low fluidity (jerky movements)
        - Incomplete tasks
        - Extended session duration
        """
        cognitive = 0.0
        
        # Speed inconsistency (25% weight)
        cognitive += min(indicators['speed_inconsistency'] * 100, 100) * 0.25
        
        # Error rate (25% weight)
        cognitive += indicators['error_count'] * 100 * 0.25
        
        # Low fluidity (20% weight)
        cognitive += (1.0 - indicators['fluidity_index']) * 100 * 0.2
        
        # Incomplete tasks (20% weight)
        cognitive += (1.0 - indicators['completion_status']) * 100 * 0.2
        
        # Duration concern (10% weight)
        cognitive += indicators['duration_concern'] * 100 * 0.1
        
        return min(cognitive, 100)
    
    def _analyze_trend(self, historical_sessions: List[Dict]) -> str:
        """Analyze wellness trend across sessions."""
        if not historical_sessions or len(historical_sessions) < 3:
            return "insufficient_data"
        
        # Get efficiency trend from last 5 sessions
        recent = historical_sessions[-5:]
        efficiencies = [s.get('analysis', {}).get('assessment', {}).get('drawing_efficiency', 50) 
                       for s in recent]
        
        if len(efficiencies) < 3:
            return "stable"
        
        # Simple trend: compare average of first half vs second half
        mid = len(efficiencies) // 2
        first_half = np.mean(efficiencies[:mid])
        second_half = np.mean(efficiencies[mid:])
        
        diff = second_half - first_half
        
        if diff > 10:
            return "improving"
        elif diff < -10:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(self, stress: float, anxiety: float, 
                                 burnout: float, cognitive_load: float) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        if stress > 70:
            recommendations.append("Take regular breaks (5-10 min every 30 min)")
            recommendations.append("Practice deep breathing or meditation")
        elif stress > 50:
            recommendations.append("Try short relaxation breaks")
        
        if anxiety > 70:
            recommendations.append("Consider grounding techniques (5-4-3-2-1 sensory method)")
            recommendations.append("Slow down your pace - focus on precision over speed")
        elif anxiety > 50:
            recommendations.append("Pause between strokes to reset focus")
        
        if burnout > 70:
            recommendations.append("Take a longer break (30+ min) before next session")
            recommendations.append("Reduce task complexity temporarily")
            recommendations.append("Reassess workload balance")
        elif burnout > 50:
            recommendations.append("Ensure adequate rest between sessions")
        
        if cognitive_load > 70:
            recommendations.append("Break tasks into smaller, manageable parts")
            recommendations.append("Reduce distractions in your environment")
        elif cognitive_load > 50:
            recommendations.append("Focus on one task at a time")
        
        if not recommendations:
            recommendations.append("Maintain current pace - doing well!")
            recommendations.append("Continue regular practice sessions")
        
        return recommendations
    
    def get_wellness_level(self, wellness_score: float) -> str:
        """Get wellness level label."""
        if wellness_score >= 80:
            return "Excellent"
        elif wellness_score >= 60:
            return "Good"
        elif wellness_score >= 40:
            return "Fair"
        elif wellness_score >= 20:
            return "Poor"
        else:
            return "Critical"


def assess_session_mental_health(session_report: Dict, historical_sessions: List[Dict] = None) -> MentalHealthProfile:
    """
    Convenience function to assess mental health from a session report.
    
    Args:
        session_report: Full session report from analysis pipeline
        historical_sessions: Previous session reports for trend analysis
        
    Returns:
        MentalHealthProfile with assessment
    """
    engine = MentalHealthAssessmentEngine()
    return engine.assess(session_report, historical_sessions)
