"""
Drawing Modality Backend API - Isolated Test Environment
=========================================================
Flask server for real-time analysis of user drawing sessions

This server:
1. Receives drawing session data from frontend (frontend/index.html)
2. Runs dynamic feature extraction (Jesun's code)
3. Runs static feature extraction (Aramide's code)
4. Returns combined analysis with scores
5. Sends results back to frontend for display

Run: python backend_api.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import traceback

# Import from local integration pipeline
from integration_pipeline import DrawingModalityPipeline
from features.mental_health_assessment import MentalHealthAssessmentEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize pipeline and mental health engine
pipeline = DrawingModalityPipeline(canvas_size=(900, 650))
mental_health_engine = MentalHealthAssessmentEngine()

# Storage for session results (in production, use database)
analysis_cache = {}
mental_health_cache = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Drawing Modality Analysis - Isolated Test',
        'version': '3.0',
        'timestamp': datetime.now().isoformat(),
        'features': {
            'dynamic': 'enabled',
            'static': 'enabled',
            'combined_scoring': 'enabled'
        }
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_session():
    """
    Analyze a drawing session.
    
    Expects JSON body with session data including:
    - sessionId
    - strokes (array of stroke objects)
    - tasks (optional - for multi-task sessions)
    
    Returns:
    - Dynamic features (20+ metrics)
    - Static features (12+ metrics)
    - Combined analysis with scores
    """
    try:
        # Get session data from request
        session_data = request.json
        
        if not session_data:
            return jsonify({
                'error': 'No session data provided',
                'status': 'failed'
            }), 400
        
        session_id = session_data.get('sessionId', 'unknown')
        print(f"\n📊 Analyzing session: {session_id}")
        print(f"   Strokes received: {len(session_data.get('strokes', []))}")
        
        # Run complete analysis
        results = pipeline.analyze_session(session_data)
        report = pipeline.generate_report(results)
        
        # Cache results
        analysis_cache[session_id] = report
        
        # Extract key metrics for response
        response = {
            'status': 'success',
            'sessionId': session_id,
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'dynamic_features': results.get('dynamic_features', {}),
                'static_features': results.get('static_features', {}),
                'combined_analysis': results.get('combined_analysis', {}),
                'validation': results.get('validation', {})
            },
            'summary': {
                'total_metrics': report['summary'].get('metrics_extracted', 0),
                'is_valid': report['summary'].get('is_complete', False),
                'errors': results.get('errors', [])
            }
        }
        
        # Add overall score if available
        if 'combined_analysis' in results:
            assessment = results['combined_analysis'].get('analysis', {}).get('overall_assessment', {})
            response['score'] = {
                'overall': assessment.get('score', 0),
                'grade': assessment.get('grade', 'N/A'),
                'efficiency': assessment.get('efficiency_component', 0),
                'quality': assessment.get('quality_component', 0)
            }
        
        print(f"✅ Analysis complete - Score: {response.get('score', {}).get('overall', 'N/A')}/100")
        print(f"   Dynamic metrics: {len(results.get('dynamic_features', {}))}")
        print(f"   Static metrics: {len(results.get('static_features', {}))}")
        
        return jsonify(response)
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error analyzing session: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'status': 'failed',
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/analyze/batch', methods=['POST'])
def analyze_batch():
    """
    Analyze multiple sessions at once.
    
    Expects JSON body with:
    - sessions: array of session objects
    
    Returns:
    - results: array of analysis results
    """
    try:
        data = request.json
        sessions = data.get('sessions', [])
        
        if not sessions:
            return jsonify({
                'error': 'No sessions provided',
                'status': 'failed'
            }), 400
        
        print(f"\n📊 Batch analysis: {len(sessions)} sessions")
        results = []
        
        for i, session in enumerate(sessions, 1):
            try:
                analysis = pipeline.analyze_session(session)
                report = pipeline.generate_report(analysis)
                
                session_id = session.get('sessionId', f'session-{i}')
                assessment = analysis.get('combined_analysis', {}).get('analysis', {}).get('overall_assessment', {})
                
                results.append({
                    'sessionId': session_id,
                    'status': 'success',
                    'score': assessment.get('score', 0),
                    'grade': assessment.get('grade', 'N/A'),
                    'metrics_extracted': report['summary'].get('metrics_extracted', 0)
                })
                
                # Cache full report
                analysis_cache[session_id] = report
                print(f"   ✅ Session {i}/{len(sessions)}: {session_id} - Score: {assessment.get('score', 0)}")
                
            except Exception as e:
                session_id = session.get('sessionId', f'session-{i}')
                print(f"   ❌ Session {i}/{len(sessions)}: {session_id} - Error: {str(e)}")
                results.append({
                    'sessionId': session_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        successful = len([r for r in results if r['status'] == 'success'])
        print(f"✅ Batch complete: {successful}/{len(sessions)} successful")
        
        return jsonify({
            'status': 'success',
            'total_sessions': len(sessions),
            'successful': successful,
            'failed': len(sessions) - successful,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/submit', methods=['POST'])
def submit_session():
    """
    Submit and save session data to Records folder.
    
    Creates folder structure:
    Records/
      SessionID/
        JSON/
          session.json
        PNG/
          task-*.png
    
    Then analyzes the session and generates report.
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'error': 'No session data provided',
                'status': 'failed'
            }), 400
        
        session_id = data.get('sessionId', f'session-{datetime.now().timestamp()}')
        tasks = data.get('tasks', {})
        
        print(f"\n📥 Submitting session: {session_id}")
        print(f"   Tasks: {len(tasks)}")
        
        # Create Records directory structure
        records_dir = Path('Records')
        session_dir = records_dir / session_id
        json_dir = session_dir / 'JSON'
        png_dir = session_dir / 'PNG'
        
        # Create directories
        json_dir.mkdir(parents=True, exist_ok=True)
        png_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON file
        json_file_path = json_dir / f'{session_id}.json'
        
        # Prepare clean data (without base64 PNG data in JSON)
        clean_data = {
            'sessionId': session_id,
            'timestamp': data.get('timestamp'),
            'type': data.get('type'),
            'totalTasks': data.get('totalTasks'),
            'tasks': {}
        }
        
        # Process each task
        for task_id, task_data in tasks.items():
            # Save PNG if present
            if 'pngData' in task_data:
                import base64
                png_file_name = task_data.get('pngFileName', f'task-{task_id}.png')
                png_file_path = png_dir / png_file_name
                
                # Decode and save PNG
                png_bytes = base64.b64decode(task_data['pngData'])
                with open(png_file_path, 'wb') as f:
                    f.write(png_bytes)
                
                print(f"   ✅ Saved PNG: {png_file_name}")
            
            # Add clean task data (without PNG base64)
            clean_task_data = {k: v for k, v in task_data.items() if k not in ['pngData', 'pngFileName']}
            clean_data['tasks'][task_id] = clean_task_data
        
        # Save JSON
        with open(json_file_path, 'w') as f:
            json.dump(clean_data, f, indent=2)
        
        print(f"   ✅ Saved JSON: {json_file_path}")
        print(f"   📁 Session saved to: {session_dir}")
        
        # Analyze the session
        print(f"   🔄 Analyzing session...")
        
        # Convert to format expected by pipeline
        analysis_session_data = {
            'sessionId': session_id,
            'timestamp': data.get('timestamp'),
            'sessionStartTime': data.get('sessionStartTime', data.get('timestamp')),
            'sessionEndTime': data.get('sessionEndTime') or data.get('timestamp') or data.get('sessionStartTime'),
            'deviceInfo': data.get('deviceInfo', {}),
            'strokes': [],
            'taskTitle': f"{len(tasks)} tasks"
        }
        
        # Combine all strokes from all tasks
        for task_id, task_data in clean_data['tasks'].items():
            if 'strokes' in task_data:
                analysis_session_data['strokes'].extend(task_data['strokes'])
        
        # Run analysis if there are strokes
        report_path = None
        if analysis_session_data['strokes']:
            results = pipeline.analyze_session(analysis_session_data)
            report = pipeline.generate_report(results)
            
            # Assess mental health based on session metrics
            mental_health_profile = mental_health_engine.assess(report)
            
            # Add mental health assessment to report
            report['mental_health_assessment'] = {
                'stress_score': mental_health_profile.stress_score,
                'anxiety_score': mental_health_profile.anxiety_score,
                'burnout_score': mental_health_profile.burnout_score,
                'cognitive_load_score': mental_health_profile.cognitive_load_score,
                'overall_wellness': mental_health_profile.overall_wellness,
                'wellness_level': mental_health_engine.get_wellness_level(mental_health_profile.overall_wellness),
                'primary_concern': mental_health_profile.primary_concern,
                'trend': mental_health_profile.trend,
                'recommendations': mental_health_profile.recommendations,
                'indicators': {k: round(v, 2) if isinstance(v, float) else v 
                              for k, v in mental_health_profile.indicators.items()}
            }
            
            print(f"   💭 Mental Health Assessment: {mental_health_profile.wellness_level} (Wellness: {mental_health_profile.overall_wellness}/100)")
            
            # Save report to session folder
            report_path = session_dir / f'{session_id}_report.json'
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"   ✅ Report generated: {report_path}")
            
            # Cache the report and mental health assessment
            analysis_cache[session_id] = report
            mental_health_cache[session_id] = mental_health_profile
        
        return jsonify({
            'status': 'success',
            'message': 'Session submitted successfully',
            'sessionId': session_id,
            'paths': {
                'session_folder': str(session_dir),
                'json_file': str(json_file_path),
                'png_folder': str(png_dir),
                'report_file': str(report_path) if report_path else None
            },
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error submitting session: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'status': 'failed',
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/report/<session_id>', methods=['GET'])
def get_report(session_id):
    """Get full report for a specific session."""
    if session_id in analysis_cache:
        return jsonify({
            'status': 'success',
            'report': analysis_cache[session_id]
        })

    report_path = Path('Records') / session_id / f'{session_id}_report.json'
    if report_path.exists():
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            analysis_cache[session_id] = report
            return jsonify({
                'status': 'success',
                'report': report
            })
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': str(e)
            }), 500

    return jsonify({
        'error': f'No report found for session {session_id}',
        'status': 'not_found'
    }), 404


@app.route('/api/export/<session_id>/<format>', methods=['GET'])
def export_report(session_id, format):
    """
    Export report in specified format.
    
    Formats: json, csv
    """
    if session_id in analysis_cache:
        report = analysis_cache[session_id]
    else:
        report_path = Path('Records') / session_id / f'{session_id}_report.json'
        if not report_path.exists():
            return jsonify({
                'error': f'No report found for session {session_id}',
                'status': 'not_found'
            }), 404
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            analysis_cache[session_id] = report
        except Exception as e:
            return jsonify({
                'status': 'failed',
                'error': str(e)
            }), 500
    
    if format == 'json':
        return jsonify(report)
    elif format == 'csv':
        # Convert to CSV format
        # This would need additional implementation
        return jsonify({
            'error': 'CSV export not yet implemented',
            'status': 'not_implemented'
        }), 501
    else:
        return jsonify({
            'error': f'Unsupported format: {format}',
            'status': 'bad_request'
        }), 400


@app.route('/api/records/<session_id>/details', methods=['GET'])
def record_details(session_id):
    """Get complete details for a saved session including report, raw session JSON, and image URLs."""
    try:
        session_dir = Path('Records') / session_id
        if not session_dir.exists() or not session_dir.is_dir():
            return jsonify({
                'status': 'not_found',
                'error': f'Session not found: {session_id}'
            }), 404

        report_file = session_dir / f'{session_id}_report.json'
        session_json_file = session_dir / 'JSON' / f'{session_id}.json'
        png_dir = session_dir / 'PNG'

        report = {}
        session_json = {}
        images = []

        if report_file.exists():
            with open(report_file, 'r') as f:
                report = json.load(f)

        if session_json_file.exists():
            with open(session_json_file, 'r') as f:
                session_json = json.load(f)

        if png_dir.exists() and png_dir.is_dir():
            for img in sorted(png_dir.glob('*.png')):
                images.append({
                    'name': img.name,
                    'url': f'/api/records/{session_id}/images/{img.name}'
                })

        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'report': report,
            'session_json': session_json,
            'images': images,
            'image_count': len(images)
        })
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': str(e)
        }), 500


@app.route('/api/records/<session_id>/images/<path:filename>', methods=['GET'])
def record_image(session_id, filename):
    """Serve PNG images for a saved session."""
    session_png_dir = Path('Records') / session_id / 'PNG'
    if not session_png_dir.exists() or not session_png_dir.is_dir():
        return jsonify({
            'status': 'not_found',
            'error': f'Image folder not found for session {session_id}'
        }), 404

    target = session_png_dir / filename
    if not target.exists() or not target.is_file():
        return jsonify({
            'status': 'not_found',
            'error': f'Image not found: {filename}'
        }), 404

    return send_from_directory(str(session_png_dir.resolve()), filename)


@app.route('/api/records', methods=['GET'])
def list_records():
    """List all saved sessions from Records folder."""
    try:
        records_dir = Path('Records')
        
        if not records_dir.exists():
            return jsonify({
                'status': 'success',
                'total': 0,
                'sessions': []
            })
        
        sessions = []
        
        # Iterate through each session folder
        for session_folder in sorted(records_dir.iterdir()):
            if not session_folder.is_dir():
                continue
            
            session_id = session_folder.name
            json_file = session_folder / 'JSON' / f'{session_id}.json'
            report_file = session_folder / f'{session_id}_report.json'
            
            # Load report if it exists
            score = 0
            grade = 'N/A'
            task_count = 0
            timestamp = datetime.now().isoformat()
            metrics_extracted = 0
            is_complete = False
            total_errors = 0
            dynamic_valid = False
            static_valid = False
            drawing_efficiency = 0
            shape_quality = 0
            total_drawing_time_ms = 0
            total_pause_time_ms = 0
            total_strokes = 0
            total_points = 0
            # Mental health fields
            stress_score = 0
            anxiety_score = 0
            burnout_score = 0
            cognitive_load_score = 0
            overall_wellness = 50
            wellness_level = 'Unknown'
            primary_concern = 'None'
            
            if report_file.exists():
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                        assessment = report.get('analysis', {}).get('assessment', {}).get('overall_assessment', {})
                        analysis_assessment = report.get('analysis', {}).get('assessment', {})
                        summary = report.get('summary', {})
                        validation = report.get('validation', {})
                        dynamic_timing = report.get('features', {}).get('dynamic', {}).get('timing', {})
                        mh_assessment = report.get('mental_health_assessment', {})

                        score = assessment.get('score', 0)
                        grade = assessment.get('grade', 'N/A')
                        timestamp = report.get('metadata', {}).get('generated_at', timestamp)
                        metrics_extracted = summary.get('metrics_extracted', 0)
                        is_complete = summary.get('is_complete', False)
                        total_errors = summary.get('total_errors', 0)
                        dynamic_valid = validation.get('dynamic', {}).get('is_valid', False)
                        static_valid = validation.get('static', {}).get('is_valid', False)
                        drawing_efficiency = analysis_assessment.get('drawing_efficiency', 0)
                        shape_quality = analysis_assessment.get('shape_quality', 0)
                        total_drawing_time_ms = dynamic_timing.get('total_drawing_time_ms', 0)
                        total_pause_time_ms = dynamic_timing.get('total_pause_time_ms', 0)
                        total_strokes = dynamic_timing.get('strokes', 0)
                        total_points = dynamic_timing.get('points', 0)
                        
                        # Extract mental health data
                        stress_score = mh_assessment.get('stress_score', 0)
                        anxiety_score = mh_assessment.get('anxiety_score', 0)
                        burnout_score = mh_assessment.get('burnout_score', 0)
                        cognitive_load_score = mh_assessment.get('cognitive_load_score', 0)
                        overall_wellness = mh_assessment.get('overall_wellness', 50)
                        wellness_level = mh_assessment.get('wellness_level', 'Unknown')
                        primary_concern = mh_assessment.get('primary_concern', 'None')
                except:
                    pass
            
            # Count PNG files (tasks)
            png_dir = session_folder / 'PNG'
            if png_dir.exists():
                task_count = len(list(png_dir.glob('*.png')))
            
            sessions.append({
                'session_id': session_id,
                'score': float(score),
                'grade': grade,
                'task_count': task_count,
                'timestamp': timestamp,
                'folder': str(session_folder),
                'metrics_extracted': int(metrics_extracted),
                'is_complete': bool(is_complete),
                'total_errors': int(total_errors),
                'dynamic_valid': bool(dynamic_valid),
                'static_valid': bool(static_valid),
                'drawing_efficiency': float(drawing_efficiency),
                'shape_quality': float(shape_quality),
                'total_drawing_time_ms': float(total_drawing_time_ms),
                'total_pause_time_ms': float(total_pause_time_ms),
                'total_strokes': int(total_strokes),
                'total_points': int(total_points),
                # Mental health metrics
                'stress_score': float(stress_score),
                'anxiety_score': float(anxiety_score),
                'burnout_score': float(burnout_score),
                'cognitive_load_score': float(cognitive_load_score),
                'overall_wellness': float(overall_wellness),
                'wellness_level': wellness_level,
                'primary_concern': primary_concern
            })
        
        return jsonify({
            'status': 'success',
            'total': len(sessions),
            'sessions': sessions
        })
    
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': str(e)
        }), 500


@app.route('/api/records/count', methods=['GET'])
def get_records_count():
    """Get count of saved sessions."""
    try:
        records_dir = Path('Records')
        
        if not records_dir.exists():
            return jsonify({
                'status': 'success',
                'count': 0
            })
        
        # Count session folders
        count = len([d for d in records_dir.iterdir() if d.is_dir()])
        
        return jsonify({
            'status': 'success',
            'count': count
        })
    
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': str(e),
            'count': 0
        }), 500


@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all analyzed sessions."""
    sessions = []
    for session_id, report in analysis_cache.items():
        assessment = report.get('analysis', {}).get('assessment', {}).get('overall_assessment', {})
        sessions.append({
            'sessionId': session_id,
            'timestamp': report.get('metadata', {}).get('generated_at', ''),
            'score': assessment.get('score', 0),
            'grade': assessment.get('grade', 'N/A'),
            'metrics': report.get('summary', {}).get('metrics_extracted', 0)
        })
    
    return jsonify({
        'status': 'success',
        'total_sessions': len(sessions),
        'sessions': sessions
    })


@app.route('/api/mental-health/<session_id>', methods=['GET'])
def get_mental_health(session_id):
    """Get comprehensive mental health assessment for a session."""
    try:
        session_dir = Path('Records') / session_id
        report_file = session_dir / f'{session_id}_report.json'
        
        if not report_file.exists():
            return jsonify({
                'status': 'not_found',
                'error': f'No report found for session {session_id}'
            }), 404
        
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        mh_data = report.get('mental_health_assessment', {})
        
        if not mh_data:
            return jsonify({
                'status': 'not_available',
                'error': 'Mental health assessment not available for this session',
                'message': 'Report was generated before mental health assessment was implemented'
            }), 404
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'assessment': mh_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║  Drawing Modality Analysis Backend API                     ║
║  Isolated Test Environment                                 ║
║  Version: 3.0 - Production Ready                          ║
╚════════════════════════════════════════════════════════════╝

📊 Features:
  ✅ Dynamic feature extraction (20+ temporal metrics)
  ✅ Static feature extraction (12+ geometric metrics)
  ✅ Combined scoring and grading
  ✅ Real-time analysis
  ✅ Batch processing

🌐 Endpoints:
  GET  /api/health                    - Health check
  POST /api/analyze                   - Analyze single session
  POST /api/analyze/batch             - Analyze multiple sessions
  POST /api/submit                    - Submit & save to Records folder
  GET  /api/records                   - List all saved records
  GET  /api/records/count             - Get count of saved sessions
  GET  /api/report/<session_id>       - Get full report
  GET  /api/export/<session_id>/<fmt> - Export report
  GET  /api/sessions                  - List all analyzed sessions

🚀 Starting server on http://localhost:5000
   Frontend: http://localhost:8000

📁 Working Directory: Drawing_Modality_Test_1/
""")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,  # Disable reloader to avoid OpenCV import issues
        threaded=True
    )
