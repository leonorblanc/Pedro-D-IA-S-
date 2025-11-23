from flask import Flask, render_template, request, send_file, jsonify

import io
import os
import random
import numpy as np
import cv2
from PIL import Image
from face_swap import swap_faces
from fun_facts import FACTS

app = Flask(__name__, static_folder='static', template_folder='templates')

# Fixed source image: place the image at `static/source.png` to use it as the
# source face for every incoming target image. If not present, uploads with a
# `source` file still work.
SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'static')
SOURCE_IMAGE_REL = os.path.join('static', 'source.png')
FIXED_SOURCE_IMG = None
FIXED_SOURCE_PATH = None
FIXED_SOURCE_MTIME = None

def load_fixed_source(force=False):
    """Try to load a fixed source image from `static/` with common extensions.
    Returns the loaded image or None."""
    global FIXED_SOURCE_IMG, FIXED_SOURCE_PATH, FIXED_SOURCE_MTIME
    exts = ['png', 'jpg', 'jpeg']
    for ext in exts:
        fn = f'source.{ext}'
        path = os.path.join(SOURCE_DIR, fn)
        if not os.path.exists(path):
            continue
        mtime = os.path.getmtime(path)
        if (not force and FIXED_SOURCE_IMG is not None and
                FIXED_SOURCE_PATH == path and FIXED_SOURCE_MTIME == mtime):
            return FIXED_SOURCE_IMG
        try:
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                print(f'Loaded fixed source image: {os.path.join("static", fn)} (via OpenCV)')
                FIXED_SOURCE_IMG = img
                FIXED_SOURCE_PATH = path
                FIXED_SOURCE_MTIME = mtime
                return img
            # If OpenCV couldn't read it, try Pillow as a fallback and convert
            try:
                pil = Image.open(path).convert('RGB')
                arr = np.array(pil)
                # convert RGB -> BGR for OpenCV compatibility
                bgr = arr[:, :, ::-1].copy()
                print(f'Loaded fixed source image: {os.path.join("static", fn)} (via Pillow fallback)')
                FIXED_SOURCE_IMG = bgr
                FIXED_SOURCE_PATH = path
                FIXED_SOURCE_MTIME = mtime
                return bgr
            except Exception as e:
                print(f'Pillow fallback failed for {path}: {e}')
        except Exception as e:
            print(f'Error reading {path}: {e}')
    print(f"Warning: fixed source image not found in {SOURCE_DIR}. Place source.png (or source.jpg) there to use fixed source.")
    FIXED_SOURCE_IMG = None
    FIXED_SOURCE_PATH = None
    FIXED_SOURCE_MTIME = None
    return None

# try to load at startup
FIXED_SOURCE_IMG = load_fixed_source()


@app.route('/debug-source')
def debug_source():
    """Return diagnostic info about fixed source image files and load status."""
    info = {}
    exts = ['png', 'jpg', 'jpeg']
    for ext in exts:
        fn = os.path.join(SOURCE_DIR, f'source.{ext}')
        info[f'file_{ext}'] = os.path.exists(fn)

    # Try to load with OpenCV and report shape if successful
    try:
        loaded = False
        for ext in exts:
            p = os.path.join(SOURCE_DIR, f'source.{ext}')
            if os.path.exists(p):
                img = cv2.imread(p, cv2.IMREAD_COLOR)
                info[f'load_{ext}'] = bool(img is not None)
                if img is not None:
                    info['loaded_ext'] = ext
                    info['shape'] = img.shape[:2]
                    loaded = True
                    break
        info['opencv_present'] = True
        info['opencv_version'] = cv2.__version__ 
        if not loaded:
            info['note'] = 'Files exist but OpenCV could not read them or no files present.'
    except Exception as e:
        info['opencv_present'] = False
        info['error'] = str(e)

    return jsonify(info)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/swap', methods=['POST'])
def swap_route():
    # Require a target image. Use an uploaded source if provided; otherwise
    # fall back to the fixed `FIXED_SOURCE_IMG` loaded at startup.
    if 'target' not in request.files:
        return jsonify({'error': 'target file required'}), 400

    tgt_file = request.files['target']
    tgt_bytes = tgt_file.read()
    tgt_arr = np.frombuffer(tgt_bytes, np.uint8)
    tgt_img = cv2.imdecode(tgt_arr, cv2.IMREAD_COLOR)
    if tgt_img is None:
        return jsonify({'error': 'could not decode target image'}), 400

    # If a source file was uploaded, prefer it.
    if 'source' in request.files and request.files['source'].filename:
        src_file = request.files['source']
        src_bytes = src_file.read()
        src_arr = np.frombuffer(src_bytes, np.uint8)
        src_img = cv2.imdecode(src_arr, cv2.IMREAD_COLOR)
        if src_img is None:
            return jsonify({'error': 'could not decode uploaded source image'}), 400
    else:
        # Refresh the cached fixed source (reloads when the file changes)
        fixed = load_fixed_source()
        if fixed is None:
            return jsonify({'error': 'fixed source image not found in static/ (expected source.png or source.jpg). Upload a source file or place an image there.'}), 500
        # Use a copy to avoid accidental modification of the in-memory image
        src_img = fixed.copy()

    try:
        output = swap_faces(src_img, tgt_img)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Encode to PNG
    is_success, buffer = cv2.imencode('.png', output)
    io_buf = io.BytesIO(buffer.tobytes())
    io_buf.seek(0)

    return send_file(io_buf, mimetype='image/png')


@app.route('/fact')
def fact():
    return jsonify({'fact': random.choice(FACTS)})


@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request: ' + str(e)}), 400

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

if __name__ == '__main__':
    # Run the Flask development server
    # For production, use: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    # Set debug=False for production to disable auto-reload and better error messages
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
