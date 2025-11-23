# Pre-Deployment Checklist for Face Swap Demo

## Before Users Access the App

- [ ] **Source face image ready**
  - [ ] Image file placed at `static/source.png` (or `source.jpg`/`source.jpeg`)
  - [ ] Image is clear, front-facing photo
  - [ ] Image file size is reasonable (< 10 MB)
  - [ ] File permissions allow reading

- [ ] **Dependencies installed**
  - [ ] Run: `python -m pip install -r requirements.txt`
  - [ ] No errors during installation
  - [ ] If MediaPipe fails, that's OK—fallback Haar cascade will be used

- [ ] **Server runs without errors**
  - [ ] Run: `python app.py`
  - [ ] No import errors or crashes
  - [ ] Console shows: "Running on http://0.0.0.0:5000"
  - [ ] Press Ctrl+C to stop

- [ ] **Website loads and looks good**
  - [ ] Open: `http://localhost:5000`
  - [ ] All sections visible (header, cards, buttons)
  - [ ] Styling displays correctly
  - [ ] No JavaScript errors in browser console (F12 → Console tab)

- [ ] **File upload works**
  - [ ] Click "Upload Photo"
  - [ ] Select a test image
  - [ ] File input accepts the image

- [ ] **Camera feature works (optional)**
  - [ ] Click "Use Camera"
  - [ ] Grant camera permission when prompted
  - [ ] Video preview shows your camera feed
  - [ ] Click "Capture" to take a photo
  - [ ] Captured image appears in result area

- [ ] **Face swap works**
  - [ ] Upload or capture a target image
  - [ ] Click "Swap Faces"
  - [ ] Result appears in the result section
  - [ ] No errors in browser console

- [ ] **Fun facts feature works**
  - [ ] Click "Get Random Fact"
  - [ ] A fact appears in the fact section

- [ ] **Error handling**
  - [ ] Try swapping without uploading an image
  - [ ] Should show a clear error message
  - [ ] Try uploading a non-image file
  - [ ] Should show an error (or be rejected by browser)

---

## Production Readiness

### For Local/Shared Network Use
- [ ] Verify `source.png` is in place
- [ ] Test with multiple browsers (Chrome, Firefox, Edge)
- [ ] Test on different devices (phone, tablet, desktop)
- [ ] Camera works on the same network (if accessing from phone/other device)

### For Public Internet Deployment
- [ ] Use HTTPS (get SSL certificate from Let's Encrypt)
- [ ] Use production WSGI server (gunicorn)
- [ ] Disable debug mode: `FLASK_DEBUG=False`
- [ ] Set up monitoring/logging
- [ ] Consider rate limiting (too many swaps = high CPU)
- [ ] Test camera access from remote devices (requires HTTPS)

### Performance Optimization
- [ ] Monitor CPU usage during face swaps
- [ ] If slow, reduce max image dimensions in `app.py`
- [ ] Consider using lower-resolution source/target images
- [ ] Implement caching if swaps are repeated with same images

---

## Quick Start Commands

**Windows Command Prompt:**
```cmd
start.bat
```

**Windows PowerShell:**
```powershell
.\start.ps1
```

**Manual:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then visit: `http://localhost:5000`

---

## After Deployment - Monitor These

1. **Server logs** – Check for errors during swaps
2. **CPU/memory usage** – Face swapping is intensive
3. **File uploads** – Ensure source.png stays in place
4. **User feedback** – Camera issues, slow performance, crashes
5. **Image files** – Clean up old uploads if storing them (not currently done)

---

## Rollback / Troubleshooting Quick Links

- **Server won't start?** → Check `requirements.txt` is installed
- **Face swap errors?** → Verify `static/source.png` exists
- **Slow swaps?** → Use smaller images or upgrade CPU
- **Camera not working?** → Use `localhost` or HTTPS
- **Dependencies failing?** → Check Python version (must be 64-bit)

---

**Status:** Ready for beta testing ✅
