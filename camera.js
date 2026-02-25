/* =============================================
   CLASSROOM FACE MONITOR — Browser Camera via getUserMedia
   The browser accesses the webcam directly (no OpenCV needed).
   Frames are sent to /analyze_frame for AI face recognition.
   ============================================= */

const CameraFeed = (() => {
    let stream = null;
    let analyzeInterval = null;
    let isActive = false;
    const ANALYZE_EVERY_MS = 3000; // send a frame for AI analysis every 3s

    // DOM refs
    let videoEl, placeholder, statusDot, statusText, btnStart, btnStop, canvas;

    function init() {
        videoEl = document.getElementById('camera-video');
        placeholder = document.getElementById('camera-placeholder');
        statusDot = document.getElementById('camera-status-dot');
        statusText = document.getElementById('camera-status-text');
        btnStart = document.getElementById('btn-start');
        btnStop = document.getElementById('btn-stop');

        if (!videoEl) return; // not on dashboard

        // Hidden canvas used to capture frames from the video
        canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;

        // If server says monitoring was already running, reconnect camera
        if (window.MONITORING_ACTIVE) {
            startMonitoring();
        }
    }

    function setActiveState(active) {
        isActive = active;
        if (statusDot) statusDot.classList.toggle('active', active);
        if (statusText) statusText.textContent = active ? 'Live' : 'Inactive';
        if (btnStart) {
            btnStart.disabled = active;
            btnStart.innerHTML = '▶ Start Monitoring';
        }
        if (btnStop) btnStop.disabled = !active;
    }

    async function startMonitoring() {
        if (btnStart) { btnStart.disabled = true; btnStart.innerHTML = '⏳ Starting…'; }

        try {
            // 1. Ask browser for camera permission
            stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: false
            });

            // 2. Show video
            videoEl.srcObject = stream;
            videoEl.play();
            videoEl.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';

            // 3. Tell server monitoring is on
            const data = await postJson('/start_monitoring');
            if (data.status !== 'success' && data.status !== 'info') {
                throw new Error(data.message || 'Server error');
            }

            setActiveState(true);
            showToast('📷 Camera active — monitoring started', 'success');

            // 4. Start sending frames to AI every few seconds
            analyzeInterval = setInterval(sendFrameForAnalysis, ANALYZE_EVERY_MS);

        } catch (err) {
            console.error('Camera start failed:', err);
            if (err.name === 'NotAllowedError') {
                showToast('❌ Camera permission denied — allow camera in browser settings', 'error');
            } else if (err.name === 'NotFoundError') {
                showToast('❌ No camera found on this device', 'error');
            } else {
                showToast('❌ ' + err.message, 'error');
            }
            if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
            setActiveState(false);
        }
    }

    async function stopMonitoring() {
        if (btnStop) { btnStop.disabled = true; btnStop.innerHTML = '⏳ Stopping…'; }

        // Stop sending frames
        if (analyzeInterval) { clearInterval(analyzeInterval); analyzeInterval = null; }

        // Stop webcam stream
        if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }

        // Hide video, show placeholder
        if (videoEl) { videoEl.srcObject = null; videoEl.style.display = 'none'; }
        if (placeholder) placeholder.style.display = 'flex';

        // Tell server
        try {
            const data = await postJson('/stop_monitoring');
            showToast('Monitoring stopped', 'info');
        } catch (e) {
            console.warn('Stop monitoring server error:', e);
        }

        setActiveState(false);
    }

    async function sendFrameForAnalysis() {
        if (!isActive || !stream || !videoEl || videoEl.readyState < 2) return;

        try {
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

            // Get JPEG base64 (strip the data:image/jpeg;base64, prefix)
            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            const b64frame = dataUrl.split(',')[1];

            const data = await postJson('/analyze_frame', { frame: b64frame });

            if (data.status === 'success' && data.faces_detected > 0) {
                data.results.forEach(r => {
                    if (r.recognized) {
                        showToast(`✅ Recognised: ${r.name} (${(r.confidence * 100).toFixed(0)}%)`, 'success');
                    } else {
                        showToast('🚨 Unknown person detected!', 'error');
                    }
                });
            }
        } catch (e) {
            console.warn('Frame analysis error:', e);
        }
    }

    return { init, startMonitoring, stopMonitoring };
})();

document.addEventListener('DOMContentLoaded', () => CameraFeed.init());
