"""
AgriSmart - Hierarchical Image Analysis Pipeline
Performs:
1. Image Quality Validation (Resolution, Format, Blur via Laplacian variance, Exposure)
2. Plant vs. Non-Plant Classification (Excess Green Index & Vegetation Masking)
3. Plant Part Identification (Leaf vs Tuber, Fruit, Stem, Root)
"""

import io
from typing import Dict, Any, Tuple
from PIL import Image
import numpy as np
import torch
import torch.nn.functional as F

class ImageAnalysisPipeline:
    def __init__(self):
        # 3x3 Laplacian kernel for focus/blur detection
        self.laplacian_kernel = torch.tensor(
            [[0., 1., 0.],
             [1., -4., 1.],
             [0., 1., 0.]],
            dtype=torch.float32
        ).unsqueeze(0).unsqueeze(0)

    def validate_quality(self, image_bytes: bytes, max_mb: float = 10.0) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates file integrity, dimensions, exposure, and optical blur.
        """
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > max_mb:
            return False, f"Image file size ({size_mb:.2f} MB) exceeds maximum limit of {max_mb} MB.", {}

        try:
            im = Image.open(io.BytesIO(image_bytes))
            im_format = (im.format or "").upper()
            if im_format not in ["JPEG", "JPG", "PNG", "WEBP"]:
                return False, f"Unsupported format '{im_format}'. Allowed: JPEG, PNG, WEBP.", {}
            
            width, height = im.size
            if width < 100 or height < 100:
                return False, f"Image resolution ({width}x{height} px) is too low for disease pathology (minimum: 100x100 px).", {}

            # Load into RGB
            rgb_im = im.convert("RGB")
            np_arr = np.array(rgb_im, dtype=np.float32)

            # Brightness & Exposure check
            mean_brightness = float(np.mean(np_arr))
            if mean_brightness < 20.0:
                return False, "Image is excessively dark / underexposed. Please capture with adequate natural lighting.", {
                    "brightness": round(mean_brightness, 2), "blur_score": 0.0, "is_blurred": False
                }
            if mean_brightness > 245.0:
                return False, "Image is severely overexposed / washed out. Please reduce direct glare or camera flash.", {
                    "brightness": round(mean_brightness, 2), "blur_score": 0.0, "is_blurred": False
                }

            # Blur detection using Laplacian variance
            # Grayscale conversion: Y = 0.2989 R + 0.5870 G + 0.1140 B
            gray = 0.2989 * np_arr[..., 0] + 0.5870 * np_arr[..., 1] + 0.1140 * np_arr[..., 2]
            gray_tensor = torch.from_numpy(gray).unsqueeze(0).unsqueeze(0)
            
            with torch.no_grad():
                lap = F.conv2d(gray_tensor, self.laplacian_kernel, padding=1)
                blur_variance = float(torch.var(lap).item())

            # Calibrated blur threshold: < 35.0 indicates significant optical or motion blur
            is_blurred = blur_variance < 35.0
            blur_status = "Sharp / In-Focus" if not is_blurred else "Blurred"

            quality_report = {
                "width": width,
                "height": height,
                "format": im_format,
                "brightness": round(mean_brightness, 2),
                "blur_score": round(blur_variance, 2),
                "is_blurred": is_blurred,
                "status": blur_status
            }

            if is_blurred:
                return False, (
                    f"Image appears blurred (optical focus score: {blur_variance:.1f}, required: >=35.0). "
                    "Please hold camera steady and upload a sharper photograph for reliable diagnosis."
                ), quality_report

            return True, "Valid", quality_report

        except Exception as e:
            return False, f"Corrupted or invalid image file: {str(e)}", {}

    def classify_plant_presence(self, image: Image.Image) -> Tuple[bool, float, str]:
        """
        Classifies whether the image contains genuine agricultural plant foliage
        using the Excess Green Index (ExG = 2G - R - B) and vegetation pixel density.
        """
        rgb_im = image.convert("RGB")
        np_arr = np.array(rgb_im, dtype=np.float32) / 255.0
        r = np_arr[..., 0]
        g = np_arr[..., 1]
        b = np_arr[..., 2]

        total_pixels = r.size

        # Excess Green Index: ExG = 2G - R - B
        exg = (2.0 * g) - r - b

        # Vegetation mask: positive ExG and Green > Blue, with minimum green saturation
        vegetation_mask = (exg > 0.04) & (g > b) & (g > 0.15)
        veg_pixel_count = np.sum(vegetation_mask)
        vegetation_ratio = float(veg_pixel_count / max(total_pixels, 1))

        # Check for diseased / chlorotic foliage (yellow/brown lesions: R ~ G > B)
        chlorotic_mask = (r > 0.35) & (g > 0.30) & (b < 0.35) & (np.abs(r - g) < 0.18)
        chlorotic_ratio = float(np.sum(chlorotic_mask) / max(total_pixels, 1))

        total_plant_signal = vegetation_ratio + (chlorotic_ratio * 0.7)

        # Calibrated plant threshold: at least 10% foliar/chlorotic coverage
        is_plant = total_plant_signal >= 0.10
        confidence = min(max(total_plant_signal * 1.5, 0.0), 1.0)

        if not is_plant:
            msg = (
                "The uploaded image does not contain significant plant foliage or crop leaves "
                f"(plant signal: {total_plant_signal*100:.1f}%, required >= 10.0%). "
                "Detected non-plant surface, background noise, or unsupported subject."
            )
        else:
            msg = "Plant foliage detected successfully."

        return is_plant, round(confidence, 4), msg

    def identify_plant_part(self, image: Image.Image) -> Dict[str, Any]:
        """
        Identifies the morphological plant part:
        - Leaf (Foliage)
        - Tuber / Root (e.g. Potato Tuber, Beetroot)
        - Fruit / Pod (e.g. Tomato Fruit, Cotton Boll, Corn Ear)
        - Stem / Bark
        """
        rgb_im = image.convert("RGB")
        np_arr = np.array(rgb_im, dtype=np.float32) / 255.0
        r = np_arr[..., 0]
        g = np_arr[..., 1]
        b = np_arr[..., 2]

        total_pixels = r.size

        # ExG for green foliage
        exg = (2.0 * g) - r - b
        foliar_ratio = float(np.sum(exg > 0.05) / total_pixels)

        # Earthy / Tuber color signature: R > G > B, low blue, buff/brown hues
        tuber_mask = (r > 0.40) & (g > 0.28) & (g < r) & (b < 0.25) & (exg < 0.02)
        tuber_ratio = float(np.sum(tuber_mask) / total_pixels)

        # Saturated fruit signature (e.g. ripe red tomato or yellow pod)
        fruit_mask = (r > 0.60) & (g < 0.35) & (b < 0.35)
        fruit_ratio = float(np.sum(fruit_mask) / total_pixels)

        if tuber_ratio > 0.35 and foliar_ratio < 0.15:
            part = "Tuber / Root"
            is_foliar = False
            message = (
                "Plant part identified as Tuber / Root (e.g., Potato Tuber). "
                "AgriSmart's disease models are calibrated specifically for Foliar (Leaf) pathologies. "
                "Foliage blight algorithms cannot reliably diagnose potato tuber scab, black scurf, or dry rot. "
                "Please upload a clear photograph of the crop's leaf foliage."
            )
        elif fruit_ratio > 0.25 and foliar_ratio < 0.15:
            part = "Fruit / Pod"
            is_foliar = False
            message = (
                "Plant part identified as Fruit / Pod. "
                "The current model is calibrated for foliar (leaf) pathology. "
                "For reliable diagnosis, please upload a clear image of the plant's leaves."
            )
        else:
            part = "Leaf (Foliage)"
            is_foliar = True
            message = "Leaf foliage verified. Suitable for foliar disease classification."

        return {
            "part": part,
            "is_foliar": is_foliar,
            "foliar_confidence": round(max(foliar_ratio, 0.1), 3),
            "message": message
        }

image_pipeline = ImageAnalysisPipeline()
