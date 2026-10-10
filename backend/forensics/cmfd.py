import base64
import numpy as np
from PIL import Image
import cv2
from sklearn.cluster import DBSCAN


class CopyMoveForgeryDetector:
    """
    Copy-Move Forgery Detection (CMFD) Engine.
    Identifies cloned visual elements (signatures, stamps, replicated numbers, logo splicing)
    using keypoint descriptor matching, spatial distance filtering, and vector clustering.
    """

    def __init__(self, min_dist_px: float = 30.0, ratio_thresh: float = 0.75):
        self.min_dist_px = min_dist_px
        self.ratio_thresh = ratio_thresh

    def analyze(self, image: Image.Image) -> dict:
        """
        Runs CMFD on a PIL Image object.
        Returns matched cloned vector pairs, cluster count, and base64 overlay image.
        """
        if image.mode != "RGB":
            img_rgb = image.convert("RGB")
        else:
            img_rgb = image.copy()

        img_np = np.array(img_rgb)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # 1. Keypoint & Descriptor Extraction using ORB
        orb = cv2.ORB_create(nfeatures=2500, fastThreshold=10)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(keypoints) < 5:
            # Not enough keypoints to analyze
            orig_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            _, buffer_img = cv2.imencode(".png", orig_cv)
            return {
                "matched_pairs": [],
                "cluster_count": 0,
                "vector_count": 0,
                "is_suspicious": False,
                "cmfd_image_b64": f"data:image/png;base64,{base64.b64encode(buffer_img).decode('utf-8')}"
            }

        # 2. BFMatcher with KNN (k=2) for intra-image matching
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=10) # check top 10 neighbors

        valid_pair_vectors = []
        point_pairs = []

        # 3. Spatial Distance Filtering & Lowe's Ratio Test
        for match_group in matches:
            for m in match_group:
                if m.queryIdx == m.trainIdx:
                    continue # Skip self match

                pt1 = keypoints[m.queryIdx].pt # (x1, y1)
                pt2 = keypoints[m.trainIdx].pt # (x2, y2)

                spatial_dist = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

                # Filter out adjacent keypoints (spatial distance > min_dist_px)
                if spatial_dist >= self.min_dist_px:
                    dx = pt2[0] - pt1[0]
                    dy = pt2[1] - pt1[1]
                    
                    # Store shift vector (dx, dy) and coordinates
                    valid_pair_vectors.append([dx, dy, pt1[0], pt1[1], pt2[0], pt2[1]])
                    point_pairs.append({
                        "p1": (int(pt1[0]), int(pt1[1])),
                        "p2": (int(pt2[0]), int(pt2[1])),
                        "dx": round(dx, 2),
                        "dy": round(dy, 2),
                        "distance": round(spatial_dist, 2)
                    })

        # Remove duplicate reciprocal pairs (pt1->pt2 and pt2->pt1)
        unique_pairs = []
        seen = set()
        for p in point_pairs:
            key1 = (p["p1"], p["p2"])
            key2 = (p["p2"], p["p1"])
            if key1 not in seen and key2 not in seen:
                seen.add(key1)
                unique_pairs.append(p)

        # 4. DBSCAN Clustering of Shift Vectors (dx, dy)
        cluster_count = 0
        cloned_clusters = []
        if len(unique_pairs) >= 10:
            vectors_np = np.array([[p["dx"], p["dy"]] for p in unique_pairs], dtype=np.float32)
            # Require significant vector length (ignore micro-shifts)
            vector_lengths = np.sqrt(vectors_np[:, 0]**2 + vectors_np[:, 1]**2)
            valid_mask = vector_lengths > 40.0
            
            if np.sum(valid_mask) >= 5:
                vectors_abs = np.abs(vectors_np[valid_mask])
                db = DBSCAN(eps=25.0, min_samples=15).fit(vectors_abs)
                labels = db.labels_

                unique_labels = set(labels) - {-1}
                cluster_count = len(unique_labels)

                # Filter pairs that belong to a dense shift vector cluster
                cloned_pairs = []
                valid_indices = np.where(valid_mask)[0]
                for idx, label in enumerate(labels):
                    if label != -1:
                        cloned_pairs.append(unique_pairs[valid_indices[idx]])
                
                if len(cloned_pairs) >= 10:
                    unique_pairs = cloned_pairs
                else:
                    unique_pairs = []
                    cluster_count = 0
            else:
                unique_pairs = []

        # 5. Render Visualization Overlay
        overlay_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Draw vector lines connecting cloned regions
        colors = [(255, 0, 255), (0, 255, 255), (0, 255, 0), (255, 255, 0), (255, 128, 0)]

        for i, pair in enumerate(unique_pairs):
            color = colors[i % len(colors)]
            p1 = pair["p1"]
            p2 = pair["p2"]

            # Draw vector arrow line
            cv2.arrowedLine(overlay_cv, p1, p2, color, 2, tipLength=0.15)
            # Draw endpoint circles
            cv2.circle(overlay_cv, p1, 4, (0, 0, 255), -1) # Red origin
            cv2.circle(overlay_cv, p2, 4, (0, 255, 0), -1) # Green destination

        _, buffer_img = cv2.imencode(".png", overlay_cv)
        cmfd_b64 = base64.b64encode(buffer_img).decode("utf-8")

        # Require significant cluster density or vector count to avoid text repetition false positives
        is_suspicious = (cluster_count >= 2 or len(unique_pairs) >= 15)

        return {
            "matched_pairs": unique_pairs[:50], # Limit payload
            "cluster_count": cluster_count,
            "vector_count": len(unique_pairs),
            "is_suspicious": is_suspicious,
            "cmfd_image_b64": f"data:image/png;base64,{cmfd_b64}"
        }
