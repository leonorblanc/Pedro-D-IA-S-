import cv2
import numpy as np
import os
import shutil
import tempfile
from urllib.request import urlretrieve
try:
    import mediapipe as mp
    mp_face = mp.solutions.face_mesh
except Exception:
    mp = None
    mp_face = None

CASCADE_NAME = 'haarcascade_frontalface_default.xml'
CASCADE_URL = 'https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml'
LOCAL_CASCADE_PATH = os.path.join(os.path.dirname(__file__), CASCADE_NAME)
TEMP_CASCADE_PATH = os.path.join(tempfile.gettempdir(), f'atlantihacks_{CASCADE_NAME}')


def _ensure_ascii_copy(path):
    """Copy the cascade to a temp directory without special characters."""
    try:
        shutil.copyfile(path, TEMP_CASCADE_PATH)
        return TEMP_CASCADE_PATH
    except Exception:
        return None


def _is_classifier_usable(path):
    clf = cv2.CascadeClassifier(path)
    return not clf.empty()


def resolve_cascade_path():
    """Return a usable path to the Haar cascade, downloading if necessary."""
    casc_dir = getattr(cv2.data, 'haarcascades', None)
    candidates = []
    if casc_dir:
        candidates.append(os.path.join(casc_dir, CASCADE_NAME))
    candidates.append(LOCAL_CASCADE_PATH)
    candidates.append(TEMP_CASCADE_PATH)

    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        if _is_classifier_usable(path):
            return path
        safe_path = _ensure_ascii_copy(path)
        if safe_path and _is_classifier_usable(safe_path):
            return safe_path

    # If nothing usable, download directly to the ASCII-safe temp location
    download_target = TEMP_CASCADE_PATH
    try:
        urlretrieve(CASCADE_URL, download_target)
    except Exception as exc:
        raise RuntimeError(f'Unable to download Haar cascade data ({CASCADE_URL}): {exc}')

    if not _is_classifier_usable(download_target):
        raise RuntimeError('Downloaded Haar cascade data is unusable.')
    return download_target


def get_landmarks(image):
    # image: BGR
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    with mp_face.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        results = face_mesh.process(img_rgb)
        if not results.multi_face_landmarks:
            return None
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = image.shape[:2]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
        return points


def apply_affine_transform(src, src_tri, dst_tri, size):
    src_tri = np.float32(src_tri)
    dst_tri = np.float32(dst_tri)
    warp_mat = cv2.getAffineTransform(src_tri, dst_tri)
    dst = cv2.warpAffine(src, warp_mat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return dst


def rect_contains(rect, point):
    x, y, w, h = rect
    px, py = point
    return px >= x and px <= x + w and py >= y and py <= y + h


def get_triangle_indices(points, subdiv):
    # subdiv is built on the target points
    triangleList = subdiv.getTriangleList()
    pts = np.array(points)
    h, w = 0, 0
    indices = []
    for t in triangleList:
        pt = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        idx = []
        valid = True
        for p in pt:
            # find index of p in pts
            distances = np.linalg.norm(pts - p, axis=1)
            min_idx = np.argmin(distances)
            if distances[min_idx] > 1.0:
                valid = False
                break
            idx.append(int(min_idx))
        if valid and len(idx) == 3:
            indices.append(tuple(idx))
    # remove duplicates
    indices = list(set(indices))
    return indices


def warp_triangle(img1, img2, t1, t2):
    # t1 and t2 are lists of three points
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))

    t1Rect = []
    t2Rect = []
    t2RectInt = []

    for i in range(3):
        t1Rect.append(((t1[i][0] - r1[0]),(t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))
        t2RectInt.append((int(t2[i][0] - r2[0]), int(t2[i][1] - r2[1])))

    mask = np.zeros((r2[3], r2[2], 3), dtype = np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2RectInt), (1.0, 1.0, 1.0), 16, 0);

    img1Rect = img1[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]

    size = (r2[2], r2[3])
    img2Rect = apply_affine_transform(img1Rect, t1Rect, t2Rect, size)

    img2Rect = img2Rect * mask

    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * (1 - mask)
    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] + img2Rect


def swap_faces(src_img, dst_img):
    """
    Replace the face in dst_img with the face from src_img.
    Both images are BGR numpy arrays.
    Returns a new image (BGR) with the swapped face.
    """
    # Try the detailed landmark-based swap if mediapipe is available
    try:
        if mp_face is not None:
            src_points = get_landmarks(src_img)
            dst_points = get_landmarks(dst_img)
            if src_points is None or dst_points is None:
                raise ValueError('Could not detect face in one of the images.')

            src_points = np.array(src_points)
            dst_points = np.array(dst_points)

            # Compute convex hull for destination
            hullIndex = cv2.convexHull(np.array(dst_points), returnPoints=False).flatten()
            hullDst = [tuple(dst_points[int(i)]) for i in hullIndex]
            hullSrc = [tuple(src_points[int(i)]) for i in hullIndex]

            # Delaunay triangulation on destination face
            rect = (0, 0, dst_img.shape[1], dst_img.shape[0])
            subdiv = cv2.Subdiv2D(rect)
            for p in dst_points:
                subdiv.insert((int(p[0]), int(p[1])))

            triangle_indices = get_triangle_indices(dst_points, subdiv)

            # Warp triangles from src to dst
            dst_img_copy = dst_img.copy().astype(np.float32)
            for tri in triangle_indices:
                t1 = [src_points[tri[0]], src_points[tri[1]], src_points[tri[2]]]
                t2 = [dst_points[tri[0]], dst_points[tri[1]], dst_points[tri[2]]]
                warp_triangle(src_img, dst_img_copy, t1, t2)

            # Create mask for seamlessClone using convex hull of destination points
            hull8U = [(int(x), int(y)) for (x, y) in hullDst]
            mask = np.zeros(dst_img.shape, dtype=dst_img.dtype)
            cv2.fillConvexPoly(mask, np.array(hull8U), (255, 255, 255))

            r = cv2.boundingRect(np.array(hull8U))
            center = (r[0] + int(r[2]/2), r[1] + int(r[3]/2))

            output = cv2.seamlessClone(np.uint8(dst_img_copy), dst_img, mask[:,:,0], center, cv2.NORMAL_CLONE)
            return output
    except Exception:
        # Fall back to simple Haar-cascade based swap below
        pass

    # Fallback: simple bounding-box based swap using Haar cascades (works without mediapipe)
    return swap_faces_simple(src_img, dst_img)


def detect_face_rect(img):
    """Detect a single face in the image and return (x,y,w,h) or None."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    casc_path = resolve_cascade_path()
    face_cascade = cv2.CascadeClassifier(casc_path)
    if face_cascade.empty():
        raise RuntimeError(f'Haar cascade data not usable at {casc_path}')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80,80))
    if len(faces) == 0:
        return None
    # choose largest face
    faces = sorted(faces, key=lambda r: r[2]*r[3], reverse=True)
    return faces[0]


def swap_faces_simple(src_img, dst_img):
    """Simpler swap: detect face rectangles, resize/crop source to dst rect and seamlessClone."""
    src_rect = detect_face_rect(src_img)
    dst_rect = detect_face_rect(dst_img)
    if dst_rect is None:
        raise ValueError('Could not detect face in target image.')
    if src_rect is None:
        # As fallback, use whole src image as face area
        sx, sy, sw, sh = 0, 0, src_img.shape[1], src_img.shape[0]
    else:
        sx, sy, sw, sh = src_rect

    dx, dy, dw, dh = dst_rect

    # Crop source face region and resize to destination face size
    src_face = src_img[sy:sy+sh, sx:sx+sw]
    if src_face.size == 0:
        raise ValueError('Source face region empty')

    # Clamp destination rectangle to image bounds and adjust target size accordingly
    y1 = max(0, dy)
    x1 = max(0, dx)
    y2 = min(dst_img.shape[0], dy + dh)
    x2 = min(dst_img.shape[1], dx + dw)
    if y2 <= y1 or x2 <= x1:
        raise ValueError('Destination face region invalid')

    roi_h = y2 - y1
    roi_w = x2 - x1

    src_face_resized = cv2.resize(src_face, (roi_w, roi_h), interpolation=cv2.INTER_LINEAR)

    # Prepare mask (ellipse) for blending within ROI
    mask = np.zeros((roi_h, roi_w), dtype=np.uint8)
    center = (roi_w // 2, roi_h // 2)
    axes = (max(1, int(roi_w * 0.45)), max(1, int(roi_h * 0.55)))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    dst_copy = dst_img.copy()
    dst_roi = dst_copy[y1:y2, x1:x2]

    try:
        blended = cv2.seamlessClone(src_face_resized, dst_roi, mask, center, cv2.NORMAL_CLONE)
    except Exception:
        blended = cv2.addWeighted(dst_roi, 0.0, src_face_resized, 1.0, 0)

    dst_copy[y1:y2, x1:x2] = blended
    return dst_copy
