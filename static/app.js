const targetInput = document.getElementById('target');
const swapBtn = document.getElementById('swapBtn');
const resultImg = document.getElementById('resultImg');
const factBtn = document.getElementById('factBtn');
const factText = document.getElementById('factText');
const swapDefaultLabel = swapBtn.textContent.trim();
const factDefaultLabel = factBtn.textContent.trim();

// Camera elements
const openCameraBtn = document.getElementById('openCameraBtn');
const cameraContainer = document.getElementById('cameraContainer');
const video = document.getElementById('video');
const captureBtn = document.getElementById('captureBtn');
const closeCameraBtn = document.getElementById('closeCameraBtn');

let cameraStream = null;
let capturedBlob = null;

async function openCamera() {
  // Check for modern API
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      video.srcObject = cameraStream;
      cameraContainer.style.display = 'block';
      return;
    } catch (e) {
      alert('Could not open camera: ' + e.message);
      return;
    }
  }

  // Try legacy prefixed APIs for older browsers
  const legacyGetUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
  if (legacyGetUserMedia) {
    legacyGetUserMedia.call(navigator, { video: true }, (stream) => {
      cameraStream = stream;
      try { video.srcObject = stream; } catch (err) { video.src = window.URL.createObjectURL(stream); }
      cameraContainer.style.display = 'block';
    }, (err) => {
      alert('Could not open camera: ' + (err && err.message ? err.message : err));
    });
    return;
  }

  // No supported getUserMedia
  const supportMsg = 'Camera not supported in this browser or context. Use Chrome, Edge or Firefox on localhost or HTTPS and allow camera permission.';
  alert(supportMsg);
}

function closeCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  video.srcObject = null;
  cameraContainer.style.display = 'none';
}

function captureImage() {
  const w = video.videoWidth;
  const h = video.videoHeight;
  if (!w || !h) {
    alert('Camera not ready');
    return;
  }
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, w, h);
  canvas.toBlob((blob) => {
    capturedBlob = blob;
    // Show preview by converting blob to object URL
    resultImg.src = URL.createObjectURL(blob);
    // close camera after capture to save resources
    closeCamera();
  }, 'image/jpeg', 0.95);
}

async function readErrorResponse(resp) {
  const contentType = resp.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      const data = await resp.json();
      return data.error || JSON.stringify(data);
    } catch (e) {
      return 'Unexpected JSON response';
    }
  }
  try {
    return await resp.text();
  } catch (e) {
    return resp.statusText || 'Unknown error';
  }
}


swapBtn.addEventListener('click', async () => {
  // prefer captured camera blob if available, otherwise file input
  if (!capturedBlob && !targetInput.files[0]) {
    alert('Please choose a target image or take a photo.');
    return;
  }

  const fd = new FormData();
  if (capturedBlob) {
    fd.append('target', capturedBlob, 'capture.jpg');
  } else {
    fd.append('target', targetInput.files[0]);
  }

  swapBtn.disabled = true;
  swapBtn.textContent = 'Working...';

  try {
    const resp = await fetch('/swap', { method: 'POST', body: fd });
    if (!resp.ok) {
      const message = await readErrorResponse(resp);
      alert('Error: ' + message);
      return;
    }
    const blob = await resp.blob();
    resultImg.src = URL.createObjectURL(blob);
    capturedBlob = null;
  } catch (e) {
    alert('Request failed: ' + e.message);
  } finally {
    swapBtn.disabled = false;
    swapBtn.textContent = swapDefaultLabel;
  }
});

// Camera button handlers
openCameraBtn.addEventListener('click', openCamera);
captureBtn.addEventListener('click', captureImage);
closeCameraBtn.addEventListener('click', closeCamera);

factBtn.addEventListener('click', async () => {
  factBtn.disabled = true;
  factBtn.textContent = 'Thinking...';
  try {
    const r = await fetch('/fact');
    const j = await r.json();
    factText.textContent = j.fact;
  } catch (e) {
    factText.textContent = 'Could not fetch a fact.';
  } finally {
    factBtn.disabled = false;
    factBtn.textContent = factDefaultLabel;
  }
});
