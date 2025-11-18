#!/usr/bin/env python3
"""Test EasyOCR for MRZ reading - should be lighter than PaddleOCR"""

import cv2
import numpy as np
import easyocr
import re

# Load the clear passport image
image_path = "/mnt/hddraid/projects/image_verifier/public/debug/debug_20251117_084309_81078f10.jpg"
print(f"Loading: {image_path}")
image = cv2.imread(image_path)

if image is None:
    print(f"ERROR: Failed to load image")
    exit(1)

print(f"Image loaded: {image.shape}")

# Extract bottom 30% where MRZ typically is
height = image.shape[0]
mrz_region = image[int(height * 0.7):, :]

print(f"MRZ region: {mrz_region.shape}")

# Initialize EasyOCR (CPU mode to avoid GPU issues)
print("\nInitializing EasyOCR (CPU mode)...")
reader = easyocr.Reader(['en'], gpu=False)

print("Running OCR on MRZ region...")
results = reader.readtext(mrz_region)

print(f"\n=== EASYOCR RAW OUTPUT ({len(results)} detections) ===")
for idx, (bbox, text, conf) in enumerate(results):
    print(f"{idx}: '{text}' (conf: {conf:.2f})")

# Extract MRZ-like lines
all_text = []
for bbox, text, conf in results:
    clean_text = text.replace(' ', '').upper()
    if len(clean_text) >= 15 and conf > 0.3:
        all_text.append(clean_text)

print(f"\n=== FILTERED TEXT ({len(all_text)} items) ===")
for i, text in enumerate(all_text):
    print(f"{i}: {text}")

# Try to find MRZ lines (30+ chars)
mrz_lines = [t for t in all_text if len(t) >= 30]

print(f"\n=== MRZ CANDIDATE LINES ({len(mrz_lines)}) ===")
for i, line in enumerate(mrz_lines, 1):
    print(f"Line {i}: {line} ({len(line)} chars)")

if len(mrz_lines) >= 2:
    print("\n✅ Found potential MRZ data!")
else:
    print("\n⚠️  Not enough MRZ lines detected")
