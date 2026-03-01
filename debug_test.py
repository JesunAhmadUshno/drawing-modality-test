"""Quick debug script to check validation errors"""
import json
from integration_pipeline import DrawingModalityPipeline

# Load test session
with open('test_data/session_json/session-task1-two-pentagon_copy.json') as f:
    session = json.load(f)

# Analyze
pipeline = DrawingModalityPipeline()
result = pipeline.analyze_session(session)

# Print validation results
print("="*70)
print("VALIDATION RESULTS")
print("="*70)
print("\nDynamic Validation:")
print(f"  Valid: {result['validation']['dynamic']['is_valid']}")
print(f"  Errors: {result['validation']['dynamic']['errors']}")
print(f"  Warnings: {result['validation']['dynamic']['warnings']}")

print("\nStatic Validation:")
print(f"  Valid: {result['validation']['static']['is_valid']}")
print(f"  Errors: {result['validation']['static']['errors']}")
print(f"  Warnings: {result['validation']['static']['warnings']}")

print("\nOverall Errors:")
print(f"  {result['errors']}")

print("\nSession Info:")
print(f"  Session ID: {result.get('session_id')}")
print(f"  Canvas Size: {result.get('canvas_size')}")
print(f"  Dynamic Features Present: {bool(result.get('dynamic_features'))}")
print(f"  Static Features Present: {bool(result.get('static_features'))}")

print("\nDynamic Features Keys:")
if result.get('dynamic_features'):
    print(f"  {list(result.get('dynamic_features').keys())}")
    if 'error' in result.get('dynamic_features'):
        print(f"  Error: {result.get('dynamic_features')['error']}")
else:
    print("  None")

print("\nStatic Features Keys:")
if result.get('static_features'):
    print(f"  {list(result.get('static_features').keys())}")
else:
    print("  None")
