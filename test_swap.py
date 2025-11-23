import sys
import os
import traceback

try:
    from face_swap import swap_faces
except Exception as e:
    print('Error importing face_swap:', e)
    traceback.print_exc()
    sys.exit(1)

import cv2

def main():
    if len(sys.argv) < 2:
        print('Usage: python test_swap.py <target_image_path> [output_path]')
        return
    target = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else 'out.png'

    src = os.path.join('static', 'source.png')
    print('Using source:', src)
    print('Using target:', target)

    if not os.path.exists(src):
        print('Source file not found:', src)
        return
    if not os.path.exists(target):
        print('Target file not found:', target)
        return

    src_img = cv2.imread(src)
    tgt_img = cv2.imread(target)
    print('cv2 version:', cv2.__version__)
    print('src_img is None?', src_img is None)
    if src_img is not None:
        print('src shape:', src_img.shape)
    print('tgt_img is None?', tgt_img is None)
    if tgt_img is not None:
        print('tgt shape:', tgt_img.shape)

    try:
        out = swap_faces(src_img, tgt_img)
        if out is None:
            print('swap_faces returned None')
            return
        ok = cv2.imwrite(out_path, out)
        print('Wrote output:', out_path, 'success=', ok)
    except Exception as e:
        print('Exception while swapping faces:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
