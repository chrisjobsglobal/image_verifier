#!/usr/bin/env python3
"""Simple test to see if PaddleOCR can read the passport MRZ"""

import cv2
import numpy as np
from paddleocr import PaddleOCR

# Load the clear passport image
image_path = "/mnt/hddraid/projects/image_verifier/public/debug/debug_20251117_084309_81078f10.jpg"
print(f"Loading: {image_path}")
image = cv2.imread(image_path)

if image is None:
    print(f"ERROR: Failed to load image from {image_path}")
    exit(1)

print(f"Image loaded: {image.shape}")

# Extract bottom 30% where MRZ typically is
height = image.shape[0]
mrz_region = image[int(height * 0.7):, :]

print(f"MRZ region: {mrz_region.shape}")

# Initialize PaddleOCR
print("Initializing PaddleOCR...")
ocr = PaddleOCR(use_angle_cls=True, lang='en')

print("Running OCR on full image...")
result_full = ocr.ocr(image)

print("\n=== FULL IMAGE RESULTS ===")
if result_full and result_full[0]:
    for idx, line in enumerate(result_full[0]):
        text = line[1][0]
        conf = line[1][1]
        print(f"{idx}: '{text}' (conf: {conf:.2f})")
else:
    print("No text found in full image")

print("\n\nRunning OCR on MRZ region...")
result_mrz = ocr.ocr(mrz_region)

print("\n=== MRZ REGION RESULTS ===")
if result_mrz and result_mrz[0]:
    for idx, line in enumerate(result_mrz[0]):
        text = line[1][0]
        conf = line[1][1]
        print(f"{idx}: '{text}' (conf: {conf:.2f})")
else:
    print("No text found in MRZ region")
