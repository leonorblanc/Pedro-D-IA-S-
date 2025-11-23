# ✨ Face Swap Demo

Welcome to the **Face Swap** application! Transform your photos with AI-powered face swapping in just a few clicks.

## 🚀 Quick Start (Windows)

### Option 1: Automatic (Easiest)
Double-click `start.bat` and open `http://localhost:5000` in your browser.

### Option 2: PowerShell
```powershell
.\start.ps1
```

### Option 3: Manual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open: **http://localhost:5000**

---

## 📸 How to Use

1. **Set up the source face** – Place a clear photo in `static/source.png`
2. **Choose a target photo**
   - Click "Upload Photo" and select an image, OR
   - Click "📷 Use Camera" to capture one
3. **Click "✨ Swap Faces"** – Watch the magic happen!
4. **Download or screenshot** your swapped result

---

## 💡 Tips for Best Results

✅ **Source face (static/source.png):**
- Clear, front-facing photo
- Good lighting
- At least 300×300 pixels

✅ **Target photos:**
- Similar angles work better
- Good lighting improves results
- 400–2000 pixels (largest side)

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Camera not working** | Use `http://localhost:5000` and allow permissions |
| **Face swap fails** | Check `static/source.png` exists; try another image |
| **Slow processing** | Use smaller images or faster CPU |
| **Can't install deps** | Ensure 64-bit Python; install [Visual C++ Redistributable](https://support.microsoft.com/help/2977003) |

---

## 📋 System Requirements

- **Windows 10+** or macOS/Linux
- **Python 3.8+** (64-bit)
- **4 GB RAM** (8+ GB recommended)
- **Modern browser** (Chrome, Edge, Firefox)

---

## ⚙️ What's Inside

- **app.py** – Flask server backend
- **face_swap.py** – Face swapping engine (with fallback)
- **static/** – Website files (CSS, JavaScript, source image)
- **templates/** – HTML pages
- **requirements.txt** – Python dependencies

---

## ℹ️ About This App

This demo uses OpenCV and optional MediaPipe to detect faces and swap them seamlessly. Results vary based on image quality and face angles. **For entertainment purposes only!**

🎓 Built as part of **AtlantiHacks** 🎓

---

**Enjoy swapping faces!** 🎬✨
