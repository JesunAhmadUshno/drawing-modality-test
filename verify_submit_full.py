import json
from datetime import datetime, timedelta
import requests

session_id = f"verify-session-{int(datetime.now().timestamp())}"
start = datetime.now()
end = start + timedelta(seconds=2)

submission = {
    "sessionId": session_id,
    "timestamp": start.isoformat(),
    "sessionStartTime": start.isoformat(),
    "sessionEndTime": end.isoformat(),
    "deviceInfo": {
        "userAgent": "verification-script",
        "deviceType": "desktop",
        "screenWidth": 1920,
        "screenHeight": 1080,
        "os": "Windows",
        "language": "en-US",
        "timestamp": start.isoformat()
    },
    "type": "PulseKey-Assessment",
    "totalTasks": 1,
    "tasks": {
        "task1": {
            "taskId": 1,
            "title": "Verification Task",
            "type": "copy",
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "strokes": [
                {
                    "strokeId": "stroke-1",
                    "points": [
                        {"x": 100, "y": 100, "timestamp": 1000},
                        {"x": 130, "y": 120, "timestamp": 1100},
                        {"x": 180, "y": 180, "timestamp": 1200},
                        {"x": 230, "y": 220, "timestamp": 1300}
                    ],
                    "startTime": start.isoformat(),
                    "endTime": (start + timedelta(milliseconds=300)).isoformat(),
                    "inputType": "stylus"
                }
            ]
        }
    }
}

response = requests.post("http://localhost:5000/api/submit", json=submission)
print("STATUS:", response.status_code)
print(response.text)
if response.ok:
    data = response.json()
    print("REPORT:", data.get("paths", {}).get("report_file"))
