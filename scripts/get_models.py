"""Download the small vision models Nightshift uses (about 40 MB) into models/.

  yunet.onnx   face detection, used for scoring and for the overlay's face tracks (OpenCV Zoo, MIT)
  sface.onnx   face recognition embeddings, used to score faces against character sheets (OpenCV Zoo, Apache 2.0)
"""
import os
import sys
import urllib.request

DEST = os.environ.get("NIGHTSHIFT_MODELS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))
FILES = {
    "yunet.onnx": "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "sface.onnx": "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}

os.makedirs(DEST, exist_ok=True)
for name, url in FILES.items():
    dst = os.path.join(DEST, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 1000:
        print("have", name)
        continue
    print("get ", name, "<-", url)
    try:
        urllib.request.urlretrieve(url, dst + ".part")
        os.replace(dst + ".part", dst)
    except Exception as e:
        print("  failed:", e, file=sys.stderr)
        sys.exit(1)
print("models in", os.path.abspath(DEST))
