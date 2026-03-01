"""
Drawing Modality Pipeline - Demo Script
========================================
Demonstrates complete analysis of a drawing session
"""
import json
from integration_pipeline import DrawingModalityPipeline

print("="*70)
print("DRAWING MODALITY ANALYSIS PIPELINE - DEMO")
print("="*70)

# Load a test session
print("\n📁 Loading test session: session-task1-two-pentagon_copy.json")
with open('test_data/session_json/session-task1-two-pentagon_copy.json') as f:
    session = json.load(f)

# Initialize pipeline
pipeline = DrawingModalityPipeline()

# Analyze the session
print("🔄 Analyzing drawing session...")
results = pipeline.analyze_session(session)

# Generate report
print("📊 Generating assessment report...")
report = pipeline.generate_report(results)

# Display results
print("\n" + "="*70)
print("ANALYSIS RESULTS")
print("="*70)

print(f"\n📋 Session: {results['session_id']}")
print(f"   Task: {session.get('taskTitle', 'Unknown')}")
print(f"   Strokes: {len(session.get('strokes', []))}")
print(f"   Canvas: {results['canvas_size']}")

print(f"\n✅ Validation:")
print(f"   Dynamic: {'✓ Valid' if results['validation']['dynamic']['is_valid'] else '✗ Invalid'}")
print(f"   Static: {'✓ Valid' if results['validation']['static']['is_valid'] else '✗ Invalid'}")

# Dynamic features summary
if results.get('dynamic_features') and 'speed' in results['dynamic_features']:
    df = results['dynamic_features']
    print(f"\n⚡ Dynamic Features:")
    print(f"   Average Speed: {df['speed']['average']:.2f} px/ms")
    print(f"   Max Speed: {df['speed']['maximum']:.2f} px/ms")
    print(f"   Drawing Time: {df['timing']['total_drawing_time_ms']:.0f} ms")
    print(f"   Pause Time: {df['timing']['total_pause_time_ms']:.0f} ms")
    print(f"   Avg Acceleration: {df['acceleration']['average']:.4f} px/ms²")

# Static features summary
if results.get('static_features'):
    sf = results['static_features']
    print(f"\n📐 Static Features:")
    print(f"   Feature Groups: {', '.join(sf.keys())}")
    if 'strokes' in sf and isinstance(sf['strokes'], dict):
        for key, val in sf['strokes'].items():
            print(f"   {key}: {val}")

# Assessment score
if report and 'analysis' in report:
    assessment = report['analysis']['assessment']['overall_assessment']
    print(f"\n🎯 Performance Assessment:")
    print(f"   Overall Score: {assessment['score']:.1f}/100")
    if 'level' in assessment:
        print(f"   Level: {assessment['level']}")
    if 'interpretation' in assessment:
        print(f"   Interpretation: {assessment['interpretation']}")

print("\n" + "="*70)
print("✅ ANALYSIS COMPLETE")
print("="*70)

# Show where exports are saved
print(f"\n📤 Reports saved to: reports/")
print(f"   - JSON: reports/test_report.json")
print(f"   - CSV: reports/test_metrics.csv")
