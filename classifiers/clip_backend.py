"""
Zero-shot classification using CLIP.

Unlike heuristics.py, this actually looks at image content by matching
the photo against text descriptions of each category - no labeled
training data or training loop required. Much more accurate than the
color/edge heuristic, and a legitimate pretrained open-source model for
the challenge's eligibility rules.

First use downloads the model (~350MB, openai/clip-vit-base-patch32)
from Hugging Face - this needs internet once; after that it's cached
locally and inference runs fully offline.

Qualcomm AI Hub publishes CLIP variants precompiled for the Snapdragon
NPU - see README.md for using one of those instead of this CPU version
for your final submission.
"""

import cv2
import numpy as np

_MODEL = None
_PROCESSOR = None
_UNAVAILABLE = False  # set True after a failed load so we don't retry every request


def _get_model():
    global _MODEL, _PROCESSOR, _UNAVAILABLE

    if _UNAVAILABLE:
        return None, None

    if _MODEL is not None:
        return _MODEL, _PROCESSOR

    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        _MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _MODEL.eval()
        return _MODEL, _PROCESSOR
    except Exception as e:  # no internet, package missing, etc.
        print(f"[clip_backend] CLIP unavailable, will fall back to heuristic: {e}")
        _UNAVAILABLE = True
        return None, None


def is_available() -> bool:
    model, _ = _get_model()
    return model is not None


def zero_shot_classify(image_bgr, label_to_prompt: dict, label_to_group: dict | None = None):
    """
    label_to_prompt: e.g. {"plastic": "a photo of plastic waste", ...}

    Returns (best_label, confidence) or (None, None) if CLIP isn't available.
    """
    model, processor = _get_model()
    if model is None:
        return None, None

    import torch  # safe to import now - _get_model() already succeeded, so torch exists

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    labels = list(label_to_prompt.keys())
    prompts = list(label_to_prompt.values())

    inputs = processor(text=prompts, images=rgb, return_tensors="pt", padding=True)

    with torch.no_grad():
        outputs = model(**inputs)
        scores = outputs.logits_per_image[0]

    if label_to_group:
        # Compare top-level categories first. Directly softmaxing all subtype
        # prompts gives categories with more labels more chances to win.
        group_names = list(dict.fromkeys(label_to_group[label] for label in labels))
        group_scores = torch.stack([
            scores[[i for i, label in enumerate(labels) if label_to_group[label] == group]].mean()
            for group in group_names
        ])
        group_probs = group_scores.softmax(dim=0)
        best_group_idx = int(torch.argmax(group_probs).item())
        best_group = group_names[best_group_idx]
        eligible = [i for i, label in enumerate(labels) if label_to_group[label] == best_group]
        best_idx = max(eligible, key=lambda i: float(scores[i].item()))
        return labels[best_idx], float(group_probs[best_group_idx].item())

    probs = scores.softmax(dim=0)
    best_idx = int(torch.argmax(probs).item())
    return labels[best_idx], float(probs[best_idx].item())
