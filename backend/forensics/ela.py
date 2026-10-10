import io
import base64
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import cv2
from scipy.stats import kurtosis


class ErrorLevelAnalysis:
    """
    Error Level Analysis (ELA) & Compression Forensics Engine.
    Detects localized compression artifacts by resaving the image at a controlled JPEG quality
    and measuring the pixel-level difference and local sliding-window variance/kurtosis.
    """

    def __init__(self, quality: int = 90, scale: float = 15.0, patch_size: int = 16):
        self.quality = quality
        self.scale = scale
        self.patch_size = patch_size

    def analyze(self, image: Image.Image) -> dict:
        """
        Runs ELA on a PIL Image object.
        Returns statistical analysis, detected anomaly bounding boxes, and base64 heatmap string.
        """
        # Convert image to RGB mode
        if image.mode != "RGB":
            img_rgb = image.convert("RGB")
        else:
            img_rgb = image.copy()

        w, h = img_rgb.size

        # Resave image in-memory at target JPEG quality
        buffer = io.BytesIO()
        img_rgb.save(buffer, format="JPEG", quality=self.quality)
        buffer.seek(0)
        resaved_img = Image.open(buffer).convert("RGB")

        # Compute absolute pixel-wise difference
        diff_img = ImageChops.difference(img_rgb, resaved_img)

        # Scale difference to enhance visibility of error
        extrema = diff_img.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1.0

        # Calculate adaptive scale factor if standard scale factor is specified
        scale_factor = self.scale
        enhanced_diff = ImageEnhance.Brightness(diff_img).enhance(scale_factor)

        # Convert enhanced diff to NumPy array for numerical analysis
        diff_np = np.array(diff_img, dtype=np.float32) # shape (H, W, 3)
        gray_diff = cv2.cvtColor(diff_np, cv2.COLOR_RGB2GRAY)

        # Compute patch-level variance and kurtosis
        patches_var = []
        anomaly_boxes = []

        patch_h = self.patch_size
        patch_w = self.patch_size

        for y in range(0, h - patch_h + 1, patch_h):
            for x in range(0, w - patch_w + 1, patch_w):
                patch = gray_diff[y : y + patch_h, x : x + patch_w]
                var_val = float(np.var(patch))
                patches_var.append(var_val)

        patches_var_np = np.array(patches_var, dtype=np.float32)
        global_var_mean = float(np.mean(patches_var_np)) if len(patches_var_np) > 0 else 0.0
        global_var_std = float(np.std(patches_var_np)) if len(patches_var_np) > 0 else 0.0
        kurt_val = float(kurtosis(patches_var_np)) if len(patches_var_np) > 0 else 0.0

        # Flag patches exceeding threshold (e.g. mean + 2.5 * std)
        variance_threshold = global_var_mean + 2.5 * (global_var_std + 1e-5)
        
        idx = 0
        for y in range(0, h - patch_h + 1, patch_h):
            for x in range(0, w - patch_w + 1, patch_w):
                if patches_var[idx] > variance_threshold and patches_var[idx] > 15.0:
                    anomaly_boxes.append({
                        "x": x,
                        "y": y,
                        "w": patch_w,
                        "h": patch_h,
                        "variance": round(patches_var[idx], 2),
                        "score": min(1.0, float(patches_var[idx] / (variance_threshold + 1e-5)))
                    })
                idx += 1

        # Create JET colormap heatmap visualization
        gray_diff_norm = cv2.normalize(gray_diff, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        enhanced_diff_np = np.array(enhanced_diff, dtype=np.uint8)
        heatmap_cv = cv2.applyColorMap(gray_diff_norm, cv2.COLORMAP_JET)

        # Blend heatmap with original for forensic overlay
        orig_cv = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
        blended_cv = cv2.addWeighted(orig_cv, 0.4, heatmap_cv, 0.6, 0)

        # Draw bounding boxes on blended ELA overlay
        for box in anomaly_boxes:
            cv2.rectangle(
                blended_cv,
                (box["x"], box["y"]),
                (box["x"] + box["w"], box["y"] + box["h"]),
                (0, 0, 255),
                2
            )

        # Encode blended image to Base64
        _, buffer_img = cv2.imencode(".png", blended_cv)
        ela_b64 = base64.b64encode(buffer_img).decode("utf-8")

        mean_error = float(np.mean(gray_diff))
        max_error = float(np.max(gray_diff))

        # ELA Tamper confidence score estimation (0 to 1)
        flagged_ratio = len(anomaly_boxes) / max(1, len(patches_var))
        is_suspicious = (flagged_ratio > 0.02) or (kurt_val > 4.0 and global_var_std > 10.0)

        return {
            "mean_error": round(mean_error, 3),
            "max_error": round(max_error, 3),
            "variance_mean": round(global_var_mean, 3),
            "variance_std": round(global_var_std, 3),
            "kurtosis": round(kurt_val, 3),
            "anomaly_boxes": anomaly_boxes,
            "anomaly_count": len(anomaly_boxes),
            "is_suspicious": is_suspicious,
            "ela_image_b64": f"data:image/png;base64,{ela_b64}"
        }
