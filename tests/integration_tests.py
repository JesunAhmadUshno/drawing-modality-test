"""
Sprint 3 - Integrated Testing Suite
====================================
Complete production testing for Drawing Modality Analysis Pipeline

Tests:
1. Component validation (dynamic + static separately)
2. Pipeline integration (combined analysis)
3. Real data testing
4. Performance benchmarking
5. Output validation

Run: python tests/integration_tests.py
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import traceback

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from integration_pipeline import DrawingModalityPipeline


class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.start_time = None
        self.end_time = None
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
        print(f"  ✅ {test_name}" + (f" - {message}" if message else ""))
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"  ❌ {test_name}")
        print(f"     Error: {error}")
    
    def add_skip(self, test_name: str, reason: str):
        self.skipped.append((test_name, reason))
        print(f"  ⏭️  {test_name} (skipped: {reason})")
    
    def summary(self) -> str:
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        passed_pct = (len(self.passed) / total * 100) if total > 0 else 0
        
        duration = (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        
        summary = f"""
{'='*70}
TEST RESULTS SUMMARY
{'='*70}
Total Tests:     {total}
✅ Passed:       {len(self.passed)} ({passed_pct:.1f}%)
❌ Failed:       {len(self.failed)}
⏭️  Skipped:     {len(self.skipped)}
Duration:        {duration:.2f}s

Status:          {"🎉 ALL TESTS PASSED" if len(self.failed) == 0 else "⚠️  SOME TESTS FAILED"}
{'='*70}
"""
        return summary


class IntegrationTest:
    """Complete integration test suite."""
    
    def __init__(self):
        self.pipeline = DrawingModalityPipeline()
        self.test_data_dir = Path("test_data")
        self.results = TestResults()
    
    def run_all(self) -> TestResults:
        """Run complete test suite."""
        print("\n" + "="*70)
        print("DRAWING MODALITY INTEGRATION TEST SUITE")
        print("="*70)
        
        self.results.start_time = time.time()
        
        print("\n📋 Running validation tests...")
        self.test_validation()
        
        print("\n🔄 Running integration tests...")
        self.test_integration()
        
        print("\n📊 Running real data tests...")
        self.test_real_data()
        
        print("\n⚡ Running performance tests...")
        self.test_performance()
        
        print("\n📤 Running export tests...")
        self.test_export()
        
        self.results.end_time = time.time()
        
        return self.results
    
    def test_validation(self):
        """Test data validation."""
        print("\n  Validation Tests:")
        
        # Test 1: Empty session validation
        try:
            empty_session = {"strokes": []}
            result = self.pipeline.analyze_session(empty_session)
            if result.get('errors'):
                self.results.add_pass("Empty session handling", "Properly detected empty data")
            else:
                self.results.add_fail("Empty session handling", "Should detect empty session")
        except Exception as e:
            self.results.add_fail("Empty session handling", str(e))
        
        # Test 2: Valid session validation
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                if not result.get('errors'):
                    self.results.add_pass("Valid session parsing", "Session loaded and parsed")
                else:
                    self.results.add_fail("Valid session parsing", str(result['errors']))
            else:
                self.results.add_skip("Valid session parsing", "Test data not found")
        except Exception as e:
            self.results.add_fail("Valid session parsing", str(e))
        
        # Test 3: Validation reporting
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                validation = result.get('validation', {})
                if validation.get('dynamic') or validation.get('static'):
                    self.results.add_pass("Validation reporting", "Both validations present")
                else:
                    self.results.add_fail("Validation reporting", "Missing validation data")
            else:
                self.results.add_skip("Validation reporting", "Test data not found")
        except Exception as e:
            self.results.add_fail("Validation reporting", str(e))
    
    def test_integration(self):
        """Test pipeline integration."""
        print("\n  Integration Tests:")
        
        # Test 1: Dynamic extraction
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                dynamic = result.get('dynamic_features', {})
                if dynamic and 'speed' in dynamic:
                    self.results.add_pass("Dynamic feature extraction", f"Extracted {len(dynamic)} feature groups")
                else:
                    self.results.add_fail("Dynamic feature extraction", "Missing dynamic features")
            else:
                self.results.add_skip("Dynamic feature extraction", "Test data not found")
        except Exception as e:
            self.results.add_fail("Dynamic feature extraction", str(e))
        
        # Test 2: Static extraction
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                static = result.get('static_features', {})
                if static and 'bounding_box' in static:
                    self.results.add_pass("Static feature extraction", f"Extracted {len(static)} feature groups")
                else:
                    self.results.add_fail("Static feature extraction", "Missing static features")
            else:
                self.results.add_skip("Static feature extraction", "Test data not found")
        except Exception as e:
            self.results.add_fail("Static feature extraction", str(e))
        
        # Test 3: Combined analysis
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                combined = result.get('combined_analysis', {})
                if combined and 'analysis' in combined:
                    self.results.add_pass("Combined analysis", "Dynamic + static successfully merged")
                else:
                    self.results.add_fail("Combined analysis", "Missing combined analysis")
            else:
                self.results.add_skip("Combined analysis", "Test data not found")
        except Exception as e:
            self.results.add_fail("Combined analysis", str(e))
        
        # Test 4: Score calculation
        try:
            session = self._load_test_session("session-task1-two-pentagon_copy.json")
            if session:
                result = self.pipeline.analyze_session(session)
                analysis = result.get('combined_analysis', {}).get('analysis', {})
                score = analysis.get('overall_assessment', {}).get('score')
                if score is not None:
                    self.results.add_pass("Score calculation", f"Score: {score}/100")
                else:
                    self.results.add_fail("Score calculation", "Missing score")
            else:
                self.results.add_skip("Score calculation", "Test data not found")
        except Exception as e:
            self.results.add_fail("Score calculation", str(e))
    
    def test_real_data(self):
        """Test with real session data."""
        print("\n  Real Data Tests:")
        
        test_files = list(self.test_data_dir.glob("session_json/*.json"))
        if not test_files:
            print("    ⏭️  No test data files found")
            return
        
        for test_file in test_files[:3]:  # Test first 3 files
            try:
                with open(test_file) as f:
                    session = json.load(f)
                
                result = self.pipeline.analyze_session(session)
                
                if not result.get('errors'):
                    metrics = result.get('combined_analysis', {}).get('total_metrics_extracted', 0)
                    self.results.add_pass(f"Session: {test_file.stem}", f"{metrics} metrics extracted")
                else:
                    self.results.add_fail(f"Session: {test_file.stem}", str(result['errors']))
            except Exception as e:
                self.results.add_fail(f"Session: {test_file.stem}", str(e))
    
    def test_performance(self):
        """Test performance benchmarks."""
        print("\n  Performance Tests:")
        
        session = self._load_test_session("session-task1-two-pentagon_copy.json")
        if not session:
            print("    ⏭️  Test data not found")
            return
        
        # Test 1: Single session analysis speed
        try:
            start = time.time()
            result = self.pipeline.analyze_session(session)
            elapsed = time.time() - start
            
            if elapsed < 5.0:  # Should complete in < 5 seconds
                self.results.add_pass("Analysis speed", f"{elapsed:.3f}s (< 5s target)")
            else:
                self.results.add_fail("Analysis speed", f"{elapsed:.3f}s (exceeds 5s target)")
        except Exception as e:
            self.results.add_fail("Analysis speed", str(e))
        
        # Test 2: Batch processing (multiple sessions)
        try:
            test_files = list(self.test_data_dir.glob("session_json/*.json"))
            if test_files:
                start = time.time()
                for test_file in test_files:
                    with open(test_file) as f:
                        sess = json.load(f)
                    self.pipeline.analyze_session(sess)
                elapsed = time.time() - start
                
                avg_time = elapsed / len(test_files)
                self.results.add_pass("Batch processing", f"{len(test_files)} sessions in {elapsed:.2f}s ({avg_time:.3f}s avg)")
            else:
                self.results.add_skip("Batch processing", "No test data")
        except Exception as e:
            self.results.add_fail("Batch processing", str(e))
    
    def test_export(self):
        """Test export functionality."""
        print("\n  Export Tests:")
        
        session = self._load_test_session("session-task1-two-pentagon_copy.json")
        if not session:
            print("    ⏭️  Test data not found")
            return
        
        result = self.pipeline.analyze_session(session)
        report = self.pipeline.generate_report(result)
        
        # Test 1: JSON export
        try:
            json_file = Path("reports/test_report.json")
            json_file.parent.mkdir(exist_ok=True)
            self.pipeline.export_to_json(report, str(json_file))
            
            if json_file.exists():
                size = json_file.stat().st_size
                self.results.add_pass("JSON export", f"Created ({size} bytes)")
                json_file.unlink()  # Cleanup
            else:
                self.results.add_fail("JSON export", "File not created")
        except Exception as e:
            self.results.add_fail("JSON export", str(e))
        
        # Test 2: CSV export
        try:
            csv_file = Path("reports/test_metrics.csv")
            csv_file.parent.mkdir(exist_ok=True)
            self.pipeline.export_to_csv(result, str(csv_file))
            
            if csv_file.exists():
                size = csv_file.stat().st_size
                self.results.add_pass("CSV export", f"Created ({size} bytes)")
                csv_file.unlink()  # Cleanup
            else:
                self.results.add_fail("CSV export", "File not created")
        except Exception as e:
            self.results.add_fail("CSV export", str(e))
    
    def _load_test_session(self, filename: str) -> Dict[str, Any]:
        """Load a test session file."""
        file_path = self.test_data_dir / "session_json" / filename
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return None


def main():
    """Run all tests."""
    tester = IntegrationTest()
    results = tester.run_all()
    
    print(results.summary())
    
    # Return exit code based on failures
    return 0 if len(results.failed) == 0 else 1


if __name__ == "__main__":
    exit(main())
