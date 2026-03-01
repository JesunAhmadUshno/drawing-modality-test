# Submit Feature Documentation

## Overview
The Submit feature allows users to save their completed drawing sessions to a structured Records folder and receive a congratulations notification.

## User Interface

### New Button
- **Location**: Assessment Summary Modal
- **Position**: Next to "Export Final Data" button
- **Label**: "Submit"  
- **Style**: Green button with success styling

### Congratulations Popup
- **Trigger**: Clicking the Submit button after successful submission
- **Design**: Green gradient background with celebratory icon (🎉)
- **Message**: "Congratulations! Your session has been successfully submitted!"
- **Auto-close**: 5 seconds (or click OK button)

## Folder Structure

When a user clicks Submit, the system creates the following structure:

```
Records/
└── SessionID/
    ├── JSON/
    │   └── session-{SessionID}.json
    ├── PNG/
    │   ├── task-1-{task-name}.png
    │   ├── task-2-{task-name}.png
    │   └── ...
    └── {SessionID}_report.json
```

### Folder Details

#### Records/
- Root folder for all submitted sessions
- Created automatically on first submission

#### SessionID/
- Unique folder for each session
- Named with timestamp: `session-{timestamp}`
- Example: `session-1772351521`

#### JSON/
- Contains the session data in JSON format
- Includes all task data, strokes, timestamps, etc.
- File name matches session ID

#### PNG/
- Contains PNG images of each completed task
- One file per task
- Named: `task-{taskID}-{task-title}.png`

#### Report File
- Automatically generated analysis report
- Named: `{SessionID}_report.json`
- Contains:
  - Dynamic feature analysis
  - Static feature analysis
  - Combined scores
  - Assessment grades

## Backend API

### Endpoint
`POST /api/submit`

### Request Format
```json
{
  "sessionId": "session-1772351521",
  "timestamp": "2026-03-01T02:52:01.000Z",
  "type": "PulseKey-Assessment",
  "totalTasks": 3,
  "tasks": {
    "task1": {
      "title": "Two-Pentagon Copy",
      "strokes": [...],
      "pngData": "base64EncodedString",
      "pngFileName": "task-task1-two-pentagon-copy.png"
    },
    ...
  }
}
```

### Response Format
```json
{
  "status": "success",
  "message": "Session submitted successfully",
  "sessionId": "session-1772351521",
  "paths": {
    "session_folder": "Records/session-1772351521",
    "json_file": "Records/session-1772351521/JSON/session-1772351521.json",
    "png_folder": "Records/session-1772351521/PNG",
    "report_file": "Records/session-1772351521/session-1772351521_report.json"
  },
  "timestamp": "2026-03-01T02:52:03.071147"
}
```

## Workflow

1. **User completes all tasks**
   - Draws on canvas for each task
   - Uses the task system to track progress

2. **Assessment Summary appears**
   - Shows all completed tasks
   - Displays "Review All", "Export Final Data", and "Submit" buttons

3. **User clicks Submit**
   - Frontend prepares session data
   - Converts canvas to PNG (base64)
   - Sends POST request to `/api/submit`

4. **Backend processes submission**
   - Creates Records folder structure
   - Saves JSON file (clean, no base64)
   - Decodes and saves PNG files
   - Runs analysis pipeline
   - Generates report
   - Returns success response

5. **Congratulations popup appears**
   - Confirms successful submission
   - Auto-closes after 5 seconds

6. **Files are saved**
   - All data persisted in Records folder
   - Ready for further analysis or archival

## Testing

Run the test script to verify the submit functionality:

```bash
python test_submit.py
```

Expected output:
```
✅ SUCCESS!
📁 Files should be saved at:
   Records\session-XXXXXXXXXX
```

## Difference from Export

### Export Final Data
- Downloads files to user's Downloads folder
- Creates a ZIP file
- Client-side only
- No backend processing
- No analysis generated

### Submit
- Saves to server's Records folder
- Creates structured folder hierarchy
- Server-side processing
- Analyzes session data
- Generates comprehensive report
- Shows congratulations notification

## Integration with Analysis Pipeline

After submission, the backend automatically:
1. Combines strokes from all tasks
2. Runs dynamic feature extraction
3. Runs static feature extraction  
4. Computes combined scores
5. Generates assessment report
6. Saves report alongside session data

This ensures every submitted session has a complete analysis report ready for review.

## Future Enhancements

Potential features for future development:
- Email notification upon successful submission
- View all submitted sessions from UI
- Reanalyze previous sessions
- Batch export of all Records
- Cloud storage integration
- Database backend instead of file system
