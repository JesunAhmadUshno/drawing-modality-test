"""
Test script for Submit functionality
"""
import requests
import json
import base64
from datetime import datetime

# API endpoint
API_URL = 'http://localhost:5000/api/submit'

# Create simple test data
session_id = f'test-session-{int(datetime.now().timestamp())}'

test_data = {
    'sessionId': session_id,
    'timestamp': datetime.now().isoformat(),
    'type': 'PulseKey-Assessment',
    'totalTasks': 1,
    'tasks': {
        'task1': {
            'title': 'Test Task',
            'taskType': 'test',
            'strokes': [
                {
                    'points': [
                        {'x': 100, 'y': 100, 'timestamp': 1000},
                        {'x': 200, 'y': 200, 'timestamp': 1100},
                        {'x': 300, 'y': 300, 'timestamp': 1200}
                    ],
                    'startTime': 1000,
                    'endTime': 1200
                }
            ],
            'pngData': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',  # 1x1 transparent PNG
            'pngFileName': 'task-task1-test.png'
        }
    }
}

print(f"🧪 Testing Submit Functionality")
print(f"Session ID: {session_id}")
print(f"API URL: {API_URL}")
print("\nSending request...")

try:
    response = requests.post(API_URL, json=test_data)
    
    if response.ok:
        result = response.json()
        print("\n✅ SUCCESS!")
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📁 Files should be saved at:")
        print(f"   {result.get('paths', {}).get('session_folder', 'N/A')}")
        
    else:
        print(f"\n❌ FAILED!")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nMake sure the backend server is running on http://localhost:5000")
