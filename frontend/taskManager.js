// Task Manager - Seamlessly integrates with v2.0-stable drawing engine
// Only activates if TASK_CONFIG is defined - fully backward compatible

class TaskManager {
    constructor() {
        if (typeof TASK_CONFIG === 'undefined') {
            this.enabled = false;
            return;
        }
        
        this.enabled = true;
        this.currentTaskId = 1;
        this.tasks = TASK_CONFIG.tasks;
        this.sessionTasks = {};
        this.timerInterval = null;
        this.timerStarted = false;
        
        this.init();
    }

    init() {
        // Initialize task storage
        this.tasks.forEach(task => {
            this.sessionTasks[task.id] = {
                taskId: task.id,
                title: task.title,
                type: task.type,
                strokes: [],
                startTime: null,
                endTime: null
            };
        });

        // Setup UI and event listeners
        this.showTaskUI();
        this.setupEventListeners();
        this.loadTask(this.currentTaskId);
    }

    showTaskUI() {
        const header = document.getElementById('taskHeader');
        const controls = document.getElementById('taskControlsSection');
        if (header) header.classList.remove('hidden');
        if (controls) controls.style.display = 'block';
    }

    setupEventListeners() {
        const nextBtn = document.getElementById('nextTaskBtn');
        const prevBtn = document.getElementById('prevTaskBtn');
        const completeBtn = document.getElementById('completeAssessmentBtn');

        if (nextBtn) nextBtn.addEventListener('click', () => this.nextTask());
        if (prevBtn) prevBtn.addEventListener('click', () => this.prevTask());
        if (completeBtn) completeBtn.addEventListener('click', () => this.completeAssessment());
    }

    loadTask(taskId) {
        const task = TASK_CONFIG.getTaskById(taskId);
        if (!task) return;

        this.currentTaskId = taskId;
        this.updateTaskHeader(task);
        this.updateInstructions(task);
        this.updateReferenceImage(task);
        this.updateHandIndicator(task);
        this.updateProgressBar();

        if (task.type === 'timed-loop') {
            this.setupTaskTimer(task.duration);
        } else {
            this.clearTaskTimer();
        }
        
        this.updateButtonStates();
    }

    updateTaskHeader(task) {
        const titleEl = document.getElementById('taskTitle');
        const seqEl = document.getElementById('currentTaskSeq');
        if (titleEl) titleEl.textContent = task.title;
        if (seqEl) seqEl.textContent = task.sequence;
    }

    updateInstructions(task) {
        const panel = document.getElementById('instructionPanel');
        if (panel) {
            panel.textContent = task.instruction;
            panel.classList.add('visible');
        }
    }

    updateReferenceImage(task) {
        const imageBox = document.getElementById('referenceImageBox');
        const refPanel = document.getElementById('referencePanel');

        if (!task.referenceImage) {
            if (refPanel) refPanel.classList.remove('visible');
            return;
        }

        if (refPanel) refPanel.classList.add('visible');
        if (imageBox) imageBox.innerHTML = `<img src="${task.referenceImage}" alt="Reference">`;
    }

    updateHandIndicator(task) {
        const indicator = document.getElementById('handIndicator');
        if (!indicator) return;

        indicator.className = 'hand-indicator';
        if (task.hand !== 'both') {
            indicator.classList.add('active', task.hand);
            indicator.textContent = task.hand.toUpperCase() + ' HAND';
        }
    }

    updateProgressBar() {
        const fill = document.getElementById('progressFill');
        if (fill) fill.style.width = (this.currentTaskId / this.tasks.length * 100) + '%';
    }

    setupTaskTimer(duration) {
        this.clearTaskTimer();
        const timerEl = document.getElementById('taskTimer');
        if (timerEl) {
            const secs = Math.ceil(duration / 1000);
            timerEl.textContent = '0:' + (secs < 10 ? '0' : '') + secs;
        }
        window.taskTimerData = { duration, started: false, timeLeft: duration / 1000 };
    }

    clearTaskTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        const timerEl = document.getElementById('taskTimer');
        if (timerEl) {
            timerEl.classList.remove('active');
            timerEl.textContent = '0:00';
        }
    }

    startTaskTimer() {
        const task = TASK_CONFIG.getTaskById(this.currentTaskId);
        if (task.type !== 'timed-loop' || !window.taskTimerData || window.taskTimerData.started) return;

        window.taskTimerData.started = true;
        let timeLeft = window.taskTimerData.duration / 1000;
        const timerEl = document.getElementById('taskTimer');
        if (timerEl) timerEl.classList.add('active');

        this.timerInterval = setInterval(() => {
            timeLeft--;
            if (timerEl) {
                const m = Math.floor(timeLeft / 60);
                const s = Math.floor(timeLeft % 60);
                timerEl.textContent = `${m}:${s.toString().padStart(2, '0')}`;
            }
            if (timeLeft <= 0) this.endTaskTimer();
        }, 1000);
    }

    endTaskTimer() {
        this.clearTaskTimer();
        const canvas = document.getElementById('drawingCanvas');
        if (canvas) canvas.style.pointerEvents = 'none';
        setTimeout(() => {
            if (confirm('Time\'s up! Move to next task?')) this.nextTask();
            else {
                const canvas = document.getElementById('drawingCanvas');
                if (canvas) canvas.style.pointerEvents = 'auto';
            }
        }, 300);
    }

    addStrokeToTask(stroke) {
        if (this.sessionTasks[this.currentTaskId]) {
            this.sessionTasks[this.currentTaskId].strokes.push(stroke);
        }
    }

    nextTask() {
        const nextTask = TASK_CONFIG.getTaskById(this.currentTaskId + 1);
        if (!nextTask) {
            this.completeAssessment();
            return;
        }

        this.sessionTasks[this.currentTaskId].endTime = new Date().toISOString();

        const canvas = document.getElementById('drawingCanvas');
        if (canvas) canvas.style.pointerEvents = 'auto';

        this.loadTask(this.currentTaskId + 1);
        
        if (window.appInstance && window.appInstance.clear) {
            window.appInstance.clear(true);
        }
    }

    prevTask() {
        if (this.currentTaskId <= 1) return;

        this.sessionTasks[this.currentTaskId].endTime = new Date().toISOString();

        const canvas = document.getElementById('drawingCanvas');
        if (canvas) canvas.style.pointerEvents = 'auto';

        this.loadTask(this.currentTaskId - 1);
        
        if (window.appInstance && window.appInstance.clear) {
            window.appInstance.clear(true);
        }
    }

    updateButtonStates() {
        const prevBtn = document.getElementById('prevTaskBtn');
        const nextBtn = document.getElementById('nextTaskBtn');
        if (prevBtn) prevBtn.disabled = this.currentTaskId <= 1;
        if (nextBtn) nextBtn.disabled = this.currentTaskId >= this.tasks.length;
    }

    completeAssessment() {
        this.sessionTasks[this.currentTaskId].endTime = new Date().toISOString();
        this.showAssessmentSummary();
    }

    showAssessmentSummary() {
        const modal = document.getElementById('assessmentModal');
        const grid = document.getElementById('taskSummaryGrid');
        if (!modal || !grid) return;

        grid.innerHTML = '';
        this.tasks.forEach(task => {
            const data = this.sessionTasks[task.id];
            const tile = document.createElement('div');
            tile.className = 'task-tile';

            if (data.strokes.length > 0) {
                const canvas = document.createElement('canvas');
                canvas.className = 'task-tile-canvas';
                this.drawTaskThumbnail(canvas, data);
                tile.appendChild(canvas);
            } else {
                const empty = document.createElement('div');
                empty.className = 'task-tile-empty';
                empty.textContent = 'No data';
                tile.appendChild(empty);
            }

            const name = document.createElement('div');
            name.className = 'task-tile-name';
            name.textContent = task.title;
            tile.appendChild(name);

            grid.appendChild(tile);
        });

        modal.classList.add('active');

        const exportBtn = document.getElementById('finalExportBtn');
        if (exportBtn) {
            exportBtn.onclick = () => this.exportSessionData();
        }

        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.submitSessionData();
                return false;
            };
        }
    }

    drawTaskThumbnail(canvas, taskData) {
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (!taskData.strokes || taskData.strokes.length === 0) return;

        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        taskData.strokes.forEach(s => {
            s.points.forEach(p => {
                minX = Math.min(minX, p.x);
                maxX = Math.max(maxX, p.x);
                minY = Math.min(minY, p.y);
                maxY = Math.max(maxY, p.y);
            });
        });

        if (minX === Infinity) return;

        const pad = 5;
        const w = Math.max(maxX - minX, 1);
        const h = Math.max(maxY - minY, 1);
        const scale = Math.min((canvas.width - 2 * pad) / w, (canvas.height - 2 * pad) / h);

        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 1;
        ctx.lineCap = 'round';

        taskData.strokes.forEach(s => {
            if (s.points.length === 0) return;
            ctx.beginPath();
            const p0 = s.points[0];
            ctx.moveTo(pad + (p0.x - minX) * scale, pad + (p0.y - minY) * scale);
            for (let i = 1; i < s.points.length; i++) {
                const p = s.points[i];
                ctx.lineTo(pad + (p.x - minX) * scale, pad + (p.y - minY) * scale);
            }
            ctx.stroke();
        });
    }

    async exportSessionData() {
        const sessionId = `assessment-${Date.now()}`;
        const timestamp = new Date().toISOString();
        const data = {
            sessionId,
            timestamp,
            type: 'PulseKey-Assessment',
            tasks: this.sessionTasks,
            totalTasks: this.tasks.length
        };

        const taskEntries = Object.entries(this.sessionTasks)
            .filter(([, taskData]) => taskData && taskData.strokes && taskData.strokes.length > 0);

        if (!window.JSZip) {
            console.warn('JSZip not available. Falling back to separate JSON and PNG downloads.');
            const jsonBlob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const jsonUrl = URL.createObjectURL(jsonBlob);
            const jsonLink = document.createElement('a');
            jsonLink.href = jsonUrl;
            jsonLink.download = `${sessionId}.json`;
            document.body.appendChild(jsonLink);
            jsonLink.click();
            document.body.removeChild(jsonLink);
            URL.revokeObjectURL(jsonUrl);

            taskEntries.forEach(([taskId, taskData]) => {
                this.exportTaskPNG(taskId, taskData);
            });
            return;
        }

        const zip = new window.JSZip();
        const rootFolder = zip.folder(sessionId);
        const jsonFolder = rootFolder.folder('JSON');
        const drawingsFolder = rootFolder.folder('Drawings');

        jsonFolder.file(`${sessionId}.json`, JSON.stringify(data, null, 2));

        taskEntries.forEach(([taskId, taskData]) => {
            const canvas = this.renderTaskCanvas(taskData);
            const dataUrl = canvas.toDataURL('image/png');
            const base64Data = dataUrl.split(',')[1];
            const safeTitle = (taskData.title || `task-${taskId}`)
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-+|-+$/g, '');
            const fileName = `task-${taskId}-${safeTitle || `task-${taskId}`}.png`;
            drawingsFolder.file(fileName, base64Data, { base64: true });
        });

        const zipBlob = await zip.generateAsync({ type: 'blob' });
        const zipUrl = URL.createObjectURL(zipBlob);
        const zipLink = document.createElement('a');
        zipLink.href = zipUrl;
        zipLink.download = `${sessionId}.zip`;
        document.body.appendChild(zipLink);
        zipLink.click();
        document.body.removeChild(zipLink);
        URL.revokeObjectURL(zipUrl);

        // Send to backend for analysis
        await this.sendToBackendForAnalysis(data);
    }

    async sendToBackendForAnalysis(sessionData) {
        const apiUrl = 'http://localhost:5000/api/analyze';
        
        console.log('📊 Sending session to backend for analysis...');
        
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sessionData)
            });

            if (!response.ok) {
                throw new Error(`Backend API error: ${response.status}`);
            }

            const results = await response.json();
            console.log('✅ Analysis complete:', results);
            
            // Display results to user
            this.displayAnalysisResults(results);
            
        } catch (error) {
            console.error('❌ Error sending to backend:', error);
            alert(`Analysis failed: ${error.message}\n\nMake sure the backend server is running on http://localhost:5000`);
        }
    }

    displayAnalysisResults(results) {
        if (results.status !== 'success') {
            alert('Analysis failed: ' + (results.error || 'Unknown error'));
            return;
        }

        const score = results.score || {};
        const summary = results.summary || {};
        
        const message = `
🎯 Analysis Complete!

Session ID: ${results.sessionId}

📊 SCORES:
━━━━━━━━━━━━━━━━━━━━━━
Overall Score:    ${score.overall || 0}/100
Grade:            ${score.grade || 'N/A'}
Efficiency:       ${score.efficiency || 0}
Quality:          ${score.quality || 0}

📈 METRICS EXTRACTED:
━━━━━━━━━━━━━━━━━━━━━━
Total Metrics:    ${summary.total_metrics || 0}
Valid Session:    ${summary.is_valid ? '✅ Yes' : '❌ No'}

Timestamp: ${new Date(results.timestamp).toLocaleString()}
        `.trim();

        alert(message);
        
        // Log full results to console for developers
        console.log('📊 Full Analysis Results:', results);
    }

    async submitSessionData() {
        const sessionId = `session-${Date.now()}`;
        const timestamp = new Date().toISOString();
        const captureSession = window.appInstance?.captureSystem?.session || null;
        const taskStartTimes = Object.values(this.sessionTasks)
            .map((task) => task.startTime)
            .filter(Boolean)
            .sort();
        const fallbackSessionStart = taskStartTimes.length > 0 ? taskStartTimes[0] : timestamp;
        const deviceInfo = captureSession?.deviceInfo || {
            userAgent: navigator.userAgent,
            deviceType: /Mobile|Android|iPhone|iPad/.test(navigator.userAgent) ? 'mobile' : 'desktop',
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            os: navigator.platform,
            language: navigator.language,
            timestamp
        };

        const taskEntries = Object.entries(this.sessionTasks)
            .filter(([, taskData]) => taskData && taskData.strokes && taskData.strokes.length > 0);

        console.log('📤 Submitting session data to backend...');

        try {
            // Prepare data with PNGs as base64
            const submissionData = {
                sessionId,
                timestamp,
                sessionStartTime: captureSession?.sessionStartTime || fallbackSessionStart,
                sessionEndTime: new Date().toISOString(),
                deviceInfo,
                type: 'PulseKey-Assessment',
                tasks: {},
                totalTasks: this.tasks.length
            };

            // Add task data with PNG images
            for (const [taskId, taskData] of taskEntries) {
                const canvas = this.renderTaskCanvas(taskData);
                const dataUrl = canvas.toDataURL('image/png');
                const base64Data = dataUrl.split(',')[1];
                const safeTitle = (taskData.title || `task-${taskId}`)
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/^-+|-+$/g, '');
                
                submissionData.tasks[taskId] = {
                    ...taskData,
                    pngData: base64Data,
                    pngFileName: `task-${taskId}-${safeTitle || `task-${taskId}`}.png`
                };
            }

            // Send to backend submit endpoint
            const response = await fetch('http://localhost:5000/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submissionData)
            });

            if (!response.ok) {
                throw new Error(`Backend API error: ${response.status}`);
            }

            const results = await response.json();
            console.log('✅ Submission successful:', results);

            // Show congratulations popup
            this.showCongratulationsPopup();
            
            // Redirect to home page after 3 seconds
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 3000);

        } catch (error) {
            console.error('❌ Error submitting session:', error);
            alert(`Submission failed: ${error.message}\n\nMake sure the backend server is running on http://localhost:5000`);
        }
    }

    showCongratulationsPopup() {
        const popup = document.getElementById('congratulationsPopup');
        if (popup) {
            popup.classList.add('active');

            const okBtn = document.getElementById('congratsOkBtn');
            if (okBtn) {
                okBtn.onclick = () => {
                    popup.classList.remove('active');
                };
            }

            // Auto-close after 5 seconds
            setTimeout(() => {
                popup.classList.remove('active');
            }, 5000);
        }
    }

    renderTaskCanvas(taskData) {
        const canvas = document.createElement('canvas');
        canvas.width = 900;
        canvas.height = 650;
        const ctx = canvas.getContext('2d');

        // White background
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Calculate bounds
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        if (taskData.strokes && taskData.strokes.length > 0) {
            taskData.strokes.forEach(stroke => {
                stroke.points.forEach(p => {
                    minX = Math.min(minX, p.x);
                    minY = Math.min(minY, p.y);
                    maxX = Math.max(maxX, p.x);
                    maxY = Math.max(maxY, p.y);
                });
            });

            // Draw strokes
            const pad = 20;
            const w = Math.max(maxX - minX, 1);
            const h = Math.max(maxY - minY, 1);
            const scale = Math.min((canvas.width - 2 * pad) / w, (canvas.height - 2 * pad) / h);

            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            taskData.strokes.forEach(stroke => {
                if (stroke.points.length === 0) return;
                ctx.beginPath();
                const p0 = stroke.points[0];
                ctx.moveTo(pad + (p0.x - minX) * scale, pad + (p0.y - minY) * scale);
                for (let i = 1; i < stroke.points.length; i++) {
                    const p = stroke.points[i];
                    ctx.lineTo(pad + (p.x - minX) * scale, pad + (p.y - minY) * scale);
                }
                ctx.stroke();
            });
        }

        return canvas;
    }

    exportTaskPNG(taskId, taskData) {
            const canvas = this.renderTaskCanvas(taskData);

            // Export as PNG
            const link = document.createElement('a');
            const safeTitle = (taskData.title || `task-${taskId}`)
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-+|-+$/g, '');
            link.download = `task-${taskId}-${safeTitle || `task-${taskId}`}.png`;
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            console.log(`✅ PNG exported: ${link.download}`);
    }
}

// Global initialization
window.taskManager = null;
document.addEventListener('DOMContentLoaded', () => {
    if (typeof TASK_CONFIG !== 'undefined') {
        window.taskManager = new TaskManager();

        // Hook into drawing app when it's ready
        const checkApp = setInterval(() => {
            if (window.appInstance) {
                clearInterval(checkApp);
                
                // Hook stroke completion → task storage
                const origEndStroke = window.appInstance.session.endStroke;
                window.appInstance.session.endStroke = function() {
                    origEndStroke.call(this);
                    if (window.taskManager && this.strokes.length > 0 && this.currentStroke === null) {
                        const lastStroke = this.strokes[this.strokes.length - 1];
                        window.taskManager.addStrokeToTask(lastStroke);
                    }
                };

                // Hook drawing start → timer start
                const origStart = window.appInstance.handleStart;
                window.appInstance.handleStart = function(e) {
                    origStart.call(this, e);
                    if (window.taskManager && window.taskManager.startTaskTimer) {
                        window.taskManager.startTaskTimer();
                    }
                };
            }
        }, 100);
    }
});
