"""
Sprint 3 - Drawing Modality Integration Pipeline
==================================================
Production-ready integration of Dynamic + Static feature extraction

This module combines:
- Jesun's Dynamic Features (temporal/behavioral metrics)
- Aramide's Static Features (geometric/shape metrics)

For complete drawing analysis and assessment.

Usage:
------
    from integration_pipeline import DrawingModalityPipeline
    
    pipeline = DrawingModalityPipeline()
    results = pipeline.analyze_session(session_data)
    report = pipeline.generate_report(results)
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Import feature extraction modules
from features.dynamic_features import (
    DynamicFeatureExtractor,
    DrawingSessionValidator as DynamicValidator
)
from features.static_features import (
    StaticFeatureExtractor,
    StaticSessionValidator,
    compute_completion_percentage
)


class DrawingModalityPipeline:
    """
    Production pipeline for complete drawing analysis.
    
    Combines dynamic (temporal) and static (geometric) features
    for comprehensive assessment.
    """
    
    def __init__(self, canvas_size: Tuple[int, int] = (900, 650)):
        """
        Initialize pipeline.
        
        Args:
            canvas_size: (width, height) tuple for canvas dimensions
        """
        self.canvas_size = canvas_size
        self.dynamic_validator = DynamicValidator()
        self.static_validator = StaticSessionValidator(require_canvas_size=False)
        
    def analyze_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a complete drawing session with both feature sets.
        
        Args:
            session: Drawing session data with strokes, timing, etc.
            
        Returns:
            Dictionary with dynamic_features, static_features, combined_analysis
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session.get('sessionId', 'unknown'),
            'canvas_size': self.canvas_size,
            'validation': {},
            'dynamic_features': {},
            'static_features': {},
            'combined_analysis': {},
            'errors': []
        }
        
        # Validate session data
        results['validation']['dynamic'] = self._validate_dynamic(session)
        results['validation']['static'] = self._validate_static(session)
        
        if results['validation']['dynamic'].get('is_valid') and results['validation']['static'].get('is_valid'):
            # Extract dynamic features
            results['dynamic_features'] = self._extract_dynamic(session)
            
            # Extract static features
            results['static_features'] = self._extract_static(session)
            
            # Combine and analyze
            results['combined_analysis'] = self._combine_features(
                results['dynamic_features'],
                results['static_features']
            )
        else:
            error_msg = "Session validation failed"
            results['errors'].append(error_msg)
        
        return results
    
    def _validate_dynamic(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Validate temporal integrity."""
        try:
            validation = self.dynamic_validator.validate_session(session)
            return {
                'is_valid': validation.is_valid,
                'errors': validation.errors,
                'warnings': validation.warnings
            }
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
    
    def _validate_static(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Validate geometric data."""
        result = self.static_validator.validate(session, canvas_size=self.canvas_size)
        return {
            'is_valid': result['is_valid'],
            'errors': result['errors'],
            'warnings': result['warnings']
        }
    
    def _extract_dynamic(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Extract dynamic/temporal features."""
        try:
            extractor = DynamicFeatureExtractor(session)
            features = extractor.extract_all_features()
            
            return {
                'speed': {
                    'average': features.avg_speed,
                    'maximum': features.max_speed,
                    'variance': features.speed_variance
                },
                'acceleration': {
                    'average': features.avg_acceleration,
                    'maximum': features.max_acceleration,
                    'variance': features.acceleration_variance
                },
                'timing': {
                    'total_drawing_time_ms': features.total_drawing_time,
                    'total_pause_time_ms': features.total_pause_time,
                    'strokes': features.total_strokes,
                    'points': features.total_points
                },
                'pauses': {
                    'count': features.number_of_pauses,
                    'average_duration_ms': features.avg_pause_duration,
                    'maximum_duration_ms': features.max_pause_duration
                },
                'rhythm': {
                    'avg_inter_stroke_interval_ms': features.avg_inter_stroke_interval,
                    'stroke_frequency_per_sec': features.stroke_frequency
                },
                'movement': {
                    'direction_changes': features.direction_changes,
                    'average_curvature': features.avg_curvature,
                    'maximum_curvature': features.max_curvature
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _extract_static(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Extract static/geometric features."""
        try:
            extractor = StaticFeatureExtractor(session, canvas_size=self.canvas_size)
            features = extractor.extract_all_features()

            points = [pt for stroke in session.get('strokes', []) for pt in stroke.get('points', [])]

            bbox_width = None
            bbox_height = None
            bbox_center = None
            if points:
                xs = [pt.get('x', 0) for pt in points]
                ys = [pt.get('y', 0) for pt in points]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                bbox_width = float(max_x - min_x)
                bbox_height = float(max_y - min_y)
                bbox_center = {
                    'x': float((min_x + max_x) / 2),
                    'y': float((min_y + max_y) / 2)
                }

            bbox_area = features.get('static_bounding_box_area')
            drawing_area = features.get('static_drawing_area')
            hull_area = features.get('convex_hull_area')

            compactness = None
            if bbox_area is not None and bbox_area > 0 and drawing_area is not None:
                compactness = float(drawing_area / bbox_area)

            solidity = None
            if hull_area is not None and hull_area > 0 and drawing_area is not None:
                solidity = float(drawing_area / hull_area)

            stroke_count = features.get('stroke_count', 0)
            total_points = len(points)

            stroke_density = None
            point_density = None
            if bbox_area is not None and bbox_area > 0:
                stroke_density = float(stroke_count / bbox_area)
                point_density = float(total_points / bbox_area)

            hu_moments = [
                features.get(f'hu_moment_{i}') for i in range(1, 8)
            ]
            
            return {
                'bounding_box': {
                    'area': features.get('static_bounding_box_area'),
                    'width': bbox_width,
                    'height': bbox_height,
                    'center': bbox_center
                },
                'strokes': {
                    'count': features.get('stroke_count'),
                    'average_length': features.get('mean_stroke_length'),
                    'total_length': features.get('total_stroke_length')
                },
                'shape': {
                    'compactness': compactness,
                    'solidity': solidity,
                    'symmetry_x': features.get('vertical_symmetry'),
                    'symmetry_y': features.get('horizontal_symmetry'),
                    'hu_moments': hu_moments
                },
                'density': {
                    'stroke_density': stroke_density,
                    'point_density': point_density
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _combine_features(self, dynamic: Dict, static: Dict) -> Dict[str, Any]:
        """
        Combine dynamic and static features for comprehensive analysis.
        """
        return {
            'feature_sets': {
                'dynamic_count': len(self._flatten_dict(dynamic)),
                'static_count': len(self._flatten_dict(static))
            },
            'total_metrics_extracted': len(self._flatten_dict(dynamic)) + len(self._flatten_dict(static)),
            'analysis': {
                'drawing_efficiency': self._calculate_efficiency(dynamic),
                'shape_quality': self._calculate_shape_quality(static),
                'overall_assessment': self._calculate_overall_score(dynamic, static)
            }
        }
    
    def _flatten_dict(self, d: Dict) -> List[Tuple[str, Any]]:
        """Flatten nested dict to count all metrics."""
        items = []
        for k, v in d.items():
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v))
            else:
                items.append((k, v))
        return items
    
    def _calculate_efficiency(self, dynamic: Dict) -> float:
        """
        Calculate drawing efficiency (0-100).
        Based on speed consistency and pause minimization.
        """
        try:
            speed_var = dynamic.get('speed', {}).get('variance', 0)
            pause_count = dynamic.get('pauses', {}).get('count', 0)
            
            # Lower variance = more efficient (0-1 scale)
            efficiency_speed = max(0, 1 - (speed_var / 1000.0))  # Normalize variance
            efficiency_pauses = max(0, 1 - (pause_count / 20.0))  # Fewer pauses is better
            
            combined = (efficiency_speed * 0.6 + efficiency_pauses * 0.4) * 100
            return round(min(100, max(0, combined)), 2)
        except:
            return 0
    
    def _calculate_shape_quality(self, static: Dict) -> float:
        """
        Calculate shape quality (0-100).
        Based on compactness and symmetry.
        """
        try:
            compactness = static.get('shape', {}).get('compactness', 0)
            symmetry_x = abs(static.get('shape', {}).get('symmetry_x', 0))
            symmetry_y = abs(static.get('shape', {}).get('symmetry_y', 0))
            
            # Combine metrics (all should be 0-1)
            quality = ((compactness * 0.5) + 
                      (symmetry_x * 0.25) + 
                      (symmetry_y * 0.25)) * 100
            return round(min(100, max(0, quality)), 2)
        except:
            return 0
    
    def _calculate_overall_score(self, dynamic: Dict, static: Dict) -> Dict[str, Any]:
        """
        Calculate overall drawing assessment (0-100).
        """
        efficiency = self._calculate_efficiency(dynamic)
        quality = self._calculate_shape_quality(static)
        
        # Weighted combination: 40% efficiency, 60% quality
        overall = (efficiency * 0.4) + (quality * 0.6)
        
        return {
            'score': round(overall, 2),
            'max_score': 100,
            'efficiency_component': efficiency,
            'quality_component': quality,
            'grade': self._score_to_grade(overall)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def generate_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.
        
        Args:
            analysis: Result from analyze_session()
            
        Returns:
            Formatted report dictionary
        """
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'session_id': analysis.get('session_id'),
                'pipeline_version': '3.0-production'
            },
            'validation': analysis.get('validation', {}),
            'features': {
                'dynamic': analysis.get('dynamic_features', {}),
                'static': analysis.get('static_features', {})
            },
            'analysis': {
                'combined': analysis.get('combined_analysis', {}),
                'assessment': analysis.get('combined_analysis', {}).get('analysis', {})
            },
            'summary': {
                'total_errors': len(analysis.get('errors', [])),
                'is_complete': len(analysis.get('errors', [])) == 0,
                'metrics_extracted': analysis.get('combined_analysis', {}).get('total_metrics_extracted', 0)
            }
        }
    
    def export_to_csv(self, analysis: Dict[str, Any], filename: str) -> bool:
        """
        Export analysis to CSV format.
        
        Args:
            analysis: Result from analyze_session()
            filename: Output filename
            
        Returns:
            True if successful
        """
        try:
            flattened = self._flatten_dict({
                'dynamic': analysis.get('dynamic_features', {}),
                'static': analysis.get('static_features', {}),
                'combined': analysis.get('combined_analysis', {})
            })
            
            df = pd.DataFrame(flattened, columns=['metric', 'value'])
            df.to_csv(filename, index=False)
            print(f"✅ Exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def export_to_json(self, analysis: Dict[str, Any], filename: str) -> bool:
        """
        Export analysis to JSON format.
        
        Args:
            analysis: Result from analyze_session()
            filename: Output filename
            
        Returns:
            True if successful
        """
        try:
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"✅ Exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False


def main():
    """Example usage and testing."""
    print("=" * 70)
    print("Drawing Modality Integration Pipeline v3.0")
    print("=" * 70)
    
    # Example: Load and analyze a test session
    test_data_path = Path("test_data/session_json/session-task1-two-pentagon_copy.json")
    
    if test_data_path.exists():
        with open(test_data_path) as f:
            session_data = json.load(f)
        
        pipeline = DrawingModalityPipeline()
        print(f"\n📊 Analyzing session: {session_data.get('sessionId', 'unknown')}")
        
        results = pipeline.analyze_session(session_data)
        report = pipeline.generate_report(results)
        
        print("\n✅ Analysis Complete!")
        print(f"Dynamic Features Extracted: {len(report['features']['dynamic'])}")
        print(f"Static Features Extracted: {len(report['features']['static'])}")
        print(f"Total Metrics: {report['summary'].get('metrics_extracted', 0)}")
        print(f"Assessment Score: {report['analysis']['assessment'].get('overall_assessment', {}).get('score', 'N/A')}")
        
        # Export results
        pipeline.export_to_json(report, "reports/analysis_report.json")
        pipeline.export_to_csv(results, "reports/metrics.csv")
        
        return report
    else:
        print(f"❌ Test data not found at {test_data_path}")
        return None


if __name__ == "__main__":
    main()
