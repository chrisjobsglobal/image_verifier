#!/usr/bin/env python3
"""Test Tesseract OCR for MRZ reading - lightweight and fast"""

import cv2
import numpy as np
import pytesseract
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

# Preprocess for MRZ: convert to grayscale, threshold, denoise
gray = cv2.cvtColor(mrz_region, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
denoised = cv2.fastNlMeansDenoising(binary)

# Use Tesseract with MRZ-optimized config
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<'

print("\nRunning Tesseract OCR...")
text = pytesseract.image_to_string(denoised, config=custom_config)

print("\n=== RAW OCR OUTPUT ===")
print(text)

# Extract MRZ-like lines (30+ chars, mostly uppercase/numbers/<)
lines = text.strip().split('\n')
mrz_lines = []

for line in lines:
    clean_line = line.strip().replace(' ', '')
    if len(clean_line) >= 30:
        # Check if it looks like MRZ (mostly uppercase, numbers, <)
        mrz_chars = sum(1 for c in clean_line if c.isupper() or c.isdigit() or c == '<')
        if mrz_chars / len(clean_line) > 0.8:
            mrz_lines.append(clean_line)

print("\n=== EXTRACTED MRZ LINES ===")
for i, line in enumerate(mrz_lines, 1):
    print(f"Line {i}: {line} ({len(line)} chars)")

# Check if it's valid TD3 format (2 lines, 44 chars each)
if len(mrz_lines) == 2 and all(len(line) == 44 for line in mrz_lines):
    print("\n✅ Valid TD3 passport MRZ detected!")
    print(f"Line 1: {mrz_lines[0]}")
    print(f"Line 2: {mrz_lines[1]}")
else:
    print(f"\n⚠️  Found {len(mrz_lines)} MRZ-like lines, but not valid TD3 format")
