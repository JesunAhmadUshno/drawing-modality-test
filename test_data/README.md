# Test Data for Aramide's Static Feature Extraction

## 📁 Directory Structure

```
test_data_for_aramide/
├── reference_images/          # Original reference images
│   ├── two-pentagon.png
│   ├── houseDrawing.png
│   └── clock drawing.jpg
│
├── user_drawings/            # Sample user drawings (to be generated manually)
│   └── [Use drawing_test_generator.html to create these]
│
├── session_json/             # JSON session data for each drawing
│   ├── session-task1-two-pentagon_copy.json
│   ├── session-task2-house_drawing_copy.json
│   └── session-task3-clock_drawing.json
│
└── paired_sets/              # Complete test sets (reference + user drawing + JSON)
    ├── task1_reference-copy/
    │   ├── reference_two-pentagon.png
    │   ├── user_drawing_task1.png (generate manually)
    │   └── session-task1-two-pentagon_copy.json
    │
    ├── task2_reference-copy/
    └── task3_freehand/
```

## 🎯 Usage Instructions for Aramide

### 1. Testing with Existing Reference Images

The `reference_images/` folder contains the original reference images from the drawing modality:
- `two-pentagon.png` - Pentagon overlap test
- `houseDrawing.png` - House drawing test
- `clock drawing.jpg` - Clock drawing test

### 2. JSON Session Data Format

Each JSON file contains:
- **Session metadata**: ID, task info, timestamps
- **Device info**: Screen size, user agent, etc.
- **Strokes**: Array of drawing strokes with points
- **Metrics**: Duration, stroke count, status
- **Events**: Session events timeline

Example structure:
```json
{
  "sessionId": "s-1234567890-test1",
  "taskId": 1,
  "taskTitle": "Two-Pentagon Copy",
  "referenceImage": "ReferanceImages/two-pentagon.png",
  "strokes": [
    {
      "strokeId": "str-1",
      "points": [{"x": 100, "y": 100, "timestamp": 123456, ...}],
      "metrics": {"totalLength": 150, "averageSpeed": 120.5, ...}
    }
  ],
  ...
}
```

### 3. Generating User Drawings

**Option A: Use the Drawing Interface (Recommended)**
1. Open `docs/index.html` in a browser
2. Draw using the canvas interface
3. Click "Export PNG" to save user drawing
4. Click "Save Session (JSON)" to save session data
5. Move files to appropriate `paired_sets/taskX/` folder

**Option B: Use Test Drawing Generator**
1. Open `drawing_test_generator.html` in browser
2. Select reference image
3. Draw your test version
4. Export both PNG and JSON
5. Files auto-named and ready for testing

### 4. Testing Your Algorithms

**Basic Test (Dummy Data):**
```python
import cv2
import json

# Load reference
reference = cv2.imread("reference_images/two-pentagon.png")

# Load user drawing (when available)
# user_drawing = cv2.imread("user_drawings/user_task1.png")

# Load session JSON
with open("session_json/session-task1-two-pentagon_copy.json") as f:
    session_data = json.load(f)

# Run your algorithms
# orb_score = calculate_orb_similarity(reference, user_drawing)
# ssim_score = calculate_ssim(reference, user_drawing)
# contour_score = calculate_contour_similarity(reference, user_drawing)
```

**With Paired Sets:**
```python
from pathlib import Path

paired_set = Path("paired_sets/task1_reference-copy")

reference = cv2.imread(str(paired_set / "reference_two-pentagon.png"))
# user_drawing = cv2.imread(str(paired_set / "user_drawing_task1.png"))

with open(paired_set / "session-task1-two-pentagon_copy.json") as f:
    session = json.load(f)

# Test all three algorithms
# results = {
#     "orb": orb_similarity(reference, user_drawing),
#     "ssim": ssim_similarity(reference, user_drawing),
#     "contour": contour_similarity(reference, user_drawing)
# }
```

### 5. Integration with Jesun's Dynamic Features

The JSON session data is compatible with Jesun's dynamic feature extraction:
```python
from backend.sprint_3_dynamic_features.dynamic_feature_extraction import DynamicFeatureExtractor

# Load session JSON
with open("session_json/session-task1-two-pentagon_copy.json") as f:
    session = json.load(f)

# Extract dynamic features
extractor = DynamicFeatureExtractor()
dynamic_features = extractor.extract_all_features(session)

# Combine with your static features
# combined_assessment = {
#     "static": static_features,
#     "dynamic": dynamic_features,
#     "final_score": weighted_average([static_score, dynamic_score])
# }
```

## 📝 File Naming Conventions

- **Reference images**: `reference_<original_name>`
- **User drawings**: `user_drawing_task<id>.png`
- **Session JSON**: `session-task<id>-<task_name>.json`
- **Paired folders**: `task<id>_<type>/`

## 🔧 Need More Test Data?

1. **Manual Generation**: Use `docs/index.html` to create real drawings
2. **Automated**: Run this script again to regenerate JSON with different parameters
3. **Real User Data**: Once Jesun connects frontend, use actual user sessions

## ✅ Ready for Monday Demo

This structure provides:
- ✅ Reference images for all 3 main tasks
- ✅ JSON session data matching drawing modality format
- ✅ Organized paired sets for algorithm testing
- ✅ Compatible with Jesun's dynamic feature extraction
- ✅ Easy to add real user drawings when available

## 📞 Questions?

Contact Jesun for:
- Frontend integration issues
- Drawing interface questions
- JSON format clarifications
- Additional test data needs

---

**Generated**: 2026-03-01 01:03:17
**Purpose**: Sprint 3 Static Feature Extraction Testing
**For**: Aramide's Algorithm Validation (ORB, SSIM, Contour Similarity)
