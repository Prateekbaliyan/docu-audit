import base64
import numpy as np
from PIL import Image
import cv2


class NoiseAnalysisEngine:
    """
    Noise Print, High-Pass Residual, and DCT Grid Misalignment Engine.
    Detects spliced content sourced from different cameras, scanners, or software tools.
    """

    def __init__(self, patch_size: int = 32, std_dev_threshold: float = 2.5):
        self.patch_size = patch_size
        self.std_dev_threshold = std_dev_threshold

    def analyze(self, image: Image.Image) -> dict:
        """
        Runs Noise Print residual analysis and DCT grid alignment test on PIL Image.
        """
        if image.mode != "RGB":
            img_rgb = image.convert("RGB")
        else:
            img_rgb = image.copy()

        img_np = np.array(img_rgb)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # 1. High-Pass Noise Residual (R = I - Filter(I))
        # Use Median Filter to estimate smooth underlying signal
        denoised = cv2.medianBlur(gray, 3)
        residual = cv2.absdiff(gray, denoised).astype(np.float32)

        # 2. Local Noise Variance Patch Analysis
        patches_var = []
        patch_size = self.patch_size

        for y in range(0, h - patch_size + 1, patch_size):
            for x in range(0, w - patch_size + 1, patch_size):
                patch = residual[y : y + patch_size, x : x + patch_size]
                patches_var.append(float(np.var(patch)))

        patches_var_np = np.array(patches_var, dtype=np.float32)
        global_mean = float(np.mean(patches_var_np)) if len(patches_var_np) > 0 else 0.0
        global_std = float(np.std(patches_var_np)) if len(patches_var_np) > 0 else 0.0

        # Flag patches exceeding noise floor threshold (require minimum noise std and variance)
        anomaly_boxes = []
        threshold = global_mean + self.std_dev_threshold * global_std
        if global_std > 12.0:
            threshold = max(threshold, 45.0)
            idx = 0
            for y in range(0, h - patch_size + 1, patch_size):
                for x in range(0, w - patch_size + 1, patch_size):
                    var_val = patches_var[idx]
                    if var_val > threshold:
                        deviation = (var_val - global_mean) / (global_std + 1e-5)
                        anomaly_boxes.append({
                            "x": x,
                            "y": y,
                            "w": patch_size,
                            "h": patch_size,
                            "variance": round(var_val, 2),
                            "deviation_sigma": round(float(deviation), 2)
                        })
                    idx += 1

        # 3. DCT 8x8 Grid Misalignment Score
        grid_shift_scores = []
        for shift in range(1, 8):
            # Calculate gradient difference along horizontal grid lines
            h1 = gray[:, shift::8]
            h2 = gray[:, shift - 1::8]
            min_w = min(h1.shape[1], h2.shape[1])
            h_diff = np.abs(h1[:, :min_w] - h2[:, :min_w])

            # Calculate gradient difference along vertical grid lines
            v1 = gray[shift::8, :]
            v2 = gray[shift - 1::8, :]
            min_h = min(v1.shape[0], v2.shape[0])
            v_diff = np.abs(v1[:min_h, :] - v2[:min_h, :])

            grid_shift_scores.append(float(np.mean(h_diff) + np.mean(v_diff)))

        dct_grid_score = float(np.max(grid_shift_scores) / (np.min(grid_shift_scores) + 1e-5)) if grid_shift_scores else 1.0
        grid_misaligned = dct_grid_score > 1.8

        # 4. Generate Visualization Overlay
        residual_norm = cv2.normalize(residual, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        heatmap_cv = cv2.applyColorMap(residual_norm, cv2.COLORMAP_TURBO)
        orig_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        blended_cv = cv2.addWeighted(orig_cv, 0.4, heatmap_cv, 0.6, 0)

        # Highlight noise anomaly boxes in yellow/orange
        for box in anomaly_boxes:
            cv2.rectangle(
                blended_cv,
                (box["x"], box["y"]),
                (box["x"] + box["w"], box["y"] + box["h"]),
                (0, 165, 255), # BGR Orange
                2
            )

        _, buffer_img = cv2.imencode(".png", blended_cv)
        noise_b64 = base64.b64encode(buffer_img).decode("utf-8")

        is_suspicious = (len(anomaly_boxes) > 0) or grid_misaligned

        return {
            "global_noise_mean": round(global_mean, 3),
            "global_noise_std": round(global_std, 3),
            "threshold_sigma": self.std_dev_threshold,
            "anomaly_boxes": anomaly_boxes,
            "anomaly_count": len(anomaly_boxes),
            "dct_grid_score": round(dct_grid_score, 3),
            "grid_misaligned": grid_misaligned,
            "is_suspicious": is_suspicious,
            "noise_image_b64": f"data:image/png;base64,{noise_b64}"
        }
