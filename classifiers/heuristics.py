"""
Offline heuristic image features.

These are simple, explainable, fully-offline signals (color, edges,
texture) used as a FALLBACK when no trained model file is present in
models/. They are intentionally simple so the app runs and demos
correctly on day one, before you've trained/downloaded real models -
see README.md for how to replace them with a proper trained classifier.

Do not present the heuristic fallback as your final "AI model" in your
submission - it's a placeholder to keep the app functional while you
train/convert the real model described in README.md.
"""

import cv2
import numpy as np


def load_image_bgr(image_bytes: bytes):
    """Decode raw image bytes (as received from an HTTP upload) into a BGR array."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image data")
    return image


def extract_features(image_bgr) -> dict:
    """Compute simple color/texture/edge statistics from an image."""
    resized = cv2.resize(image_bgr, (256, 256))
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    h, s, v = cv2.split(hsv)

    # Green ratio - rough proxy for organic/plant matter
    green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
    green_ratio = float(np.mean(green_mask > 0))

    # Brightness / saturation - rough proxy for plastic (glossy, saturated)
    # vs paper (dull, low saturation) vs metal (low saturation, high brightness)
    mean_saturation = float(np.mean(s)) / 255.0
    mean_brightness = float(np.mean(v)) / 255.0

    # Edge density - rough proxy for clutter / texture complexity
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.mean(edges > 0))

    # Color variance across the frame - rough proxy for "many different
    # objects" (useful for the bin-overflow heuristic)
    color_std = float(np.std(resized))

    return {
        "green_ratio": green_ratio,
        "mean_saturation": mean_saturation,
        "mean_brightness": mean_brightness,
        "edge_density": edge_density,
        "color_std": color_std,
    }
