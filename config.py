"""
Production Configuration for Drawing Modality Pipeline
======================================================

Settings for different environments (development, testing, production)
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class CanvasConfig:
    """Canvas and rendering configuration."""
    width: int = 900
    height: int = 650
    stroke_width: int = 3
    background_color: str = "#FFFFFF"


@dataclass
class FeatureConfig:
    """Feature extraction configuration."""
    
    # Dynamic features
    compute_dynamic: bool = True
    speed_window_size: int = 5  # points for speed calculation
    acceleration_window_size: int = 5
    
    # Static features
    compute_static: bool = True
    use_sift: bool = True  # Requires opencv-contrib-python
    use_orb: bool = True
    use_ssim: bool = True
    use_contour: bool = True
    max_orb_matches: int = 200
    
    # Validation
    validate_temporal: bool = True
    validate_geometric: bool = True
    strict_validation: bool = False  # If True, fail on warnings


@dataclass
class ExportConfig:
    """Export and output configuration."""
    
    # Formats
    export_json: bool = True
    export_csv: bool = True
    export_pdf: bool = False
    
    # Options
    pretty_json: bool = True
    include_metadata: bool = True
    include_raw_features: bool = True
    
    # Paths
    report_dir: str = "reports"
    data_dir: str = "test_data"


@dataclass
class ScoringConfig:
    """Assessment scoring configuration."""
    
    # Weights for combined score
    efficiency_weight: float = 0.4
    quality_weight: float = 0.6
    
    # Component weights
    speed_weight: float = 0.3
    pause_weight: float = 0.3
    rhythm_weight: float = 0.4
    
    shape_weight: float = 0.5
    symmetry_weight: float = 0.5
    
    # Grade thresholds
    grade_a_min: float = 90.0
    grade_b_min: float = 80.0
    grade_c_min: float = 70.0
    grade_d_min: float = 60.0


class ProductionConfig:
    """Complete production configuration."""
    
    def __init__(self, environment: str = "production"):
        """
        Initialize configuration.
        
        Args:
            environment: "development", "testing", or "production"
        """
        self.environment = environment
        self.canvas = CanvasConfig()
        self.features = FeatureConfig()
        self.export = ExportConfig()
        self.scoring = ScoringConfig()
        
        # Environment-specific settings
        if environment == "development":
            self.features.strict_validation = False
            self.export.pretty_json = True
        elif environment == "testing":
            self.features.strict_validation = True
            self.export.include_raw_features = True
        elif environment == "production":
            self.features.strict_validation = True
            self.export.include_raw_features = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'canvas': {
                'width': self.canvas.width,
                'height': self.canvas.height,
                'stroke_width': self.canvas.stroke_width
            },
            'features': {
                'compute_dynamic': self.features.compute_dynamic,
                'compute_static': self.features.compute_static,
                'validate_temporal': self.features.validate_temporal,
                'validate_geometric': self.features.validate_geometric,
                'strict_validation': self.features.strict_validation
            },
            'export': {
                'formats': {
                    'json': self.export.export_json,
                    'csv': self.export.export_csv,
                    'pdf': self.export.export_pdf
                }
            },
            'scoring': {
                'efficiency_weight': self.scoring.efficiency_weight,
                'quality_weight': self.scoring.quality_weight
            }
        }
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate configuration.
        
        Returns:
            (is_valid, error_message)
        """
        # Check weights sum to 1.0
        total_weight = self.scoring.efficiency_weight + self.scoring.quality_weight
        if abs(total_weight - 1.0) > 0.01:
            return False, f"Weights don't sum to 1.0: {total_weight}"
        
        # Check grade thresholds are in order
        if not (0 <= self.scoring.grade_d_min < self.scoring.grade_c_min < 
                self.scoring.grade_b_min < self.scoring.grade_a_min <= 100):
            return False, "Grade thresholds not in correct order"
        
        # Check canvas size
        if self.canvas.width <= 0 or self.canvas.height <= 0:
            return False, "Canvas dimensions must be positive"
        
        return True, "Configuration valid"


# Predefined configurations
DEVELOPMENT_CONFIG = ProductionConfig("development")
TESTING_CONFIG = ProductionConfig("testing")
PRODUCTION_CONFIG = ProductionConfig("production")

# Default configuration
DEFAULT_CONFIG = PRODUCTION_CONFIG
