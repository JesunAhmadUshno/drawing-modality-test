"""
static_feature_extraction.py
Static feature extraction module for drawing sessions.

Features:
- Bounding box area
- Drawing area (rasterized)
- Stroke length stats
- Stroke density
- Compactness, solidity, convex hull
- Hu moments, symmetry

Dependencies: numpy, pandas, opencv-python (cv2), scikit-image
Optional: opencv-contrib-python (SIFT)
"""
import numpy as np
import pandas as pd
import cv2
from skimage.metrics import structural_similarity as ssim


class StaticSessionValidator:
    def __init__(self, require_canvas_size=True):
        self.require_canvas_size = require_canvas_size

    def validate(self, session, canvas_size=None):
        errors = []
        warnings = []

        if not isinstance(session, dict):
            errors.append("session must be a dict")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        strokes = session.get("strokes")
        if strokes is None or not isinstance(strokes, list):
            errors.append("session.strokes must be a list")
        else:
            for s_idx, stroke in enumerate(strokes):
                if not isinstance(stroke, dict):
                    errors.append(f"stroke[{s_idx}] must be a dict")
                    continue
                points = stroke.get("points")
                if points is None or not isinstance(points, list):
                    errors.append(f"stroke[{s_idx}].points must be a list")
                    continue
                for p_idx, pt in enumerate(points):
                    if not isinstance(pt, dict):
                        errors.append(f"stroke[{s_idx}].points[{p_idx}] must be a dict")
                        continue
                    if "x" not in pt or "y" not in pt:
                        errors.append(f"stroke[{s_idx}].points[{p_idx}] missing x/y")
                        continue
                    if not isinstance(pt["x"], (int, float)) or not isinstance(pt["y"], (int, float)):
                        errors.append(f"stroke[{s_idx}].points[{p_idx}] x/y must be numeric")

        if self.require_canvas_size and not canvas_size:
            errors.append("canvas_size must be provided")
        if canvas_size:
            if not isinstance(canvas_size, (tuple, list)) or len(canvas_size) != 2:
                errors.append("canvas_size must be a (width, height) tuple")
            else:
                w, h = canvas_size
                if not isinstance(w, (int, float)) or not isinstance(h, (int, float)):
                    errors.append("canvas_size values must be numeric")

        if not errors and strokes == []:
            warnings.append("session has no strokes")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _preprocess_binary(img):
    if img is None:
        return None
    img = (img > 0).astype(np.uint8) * 255
    img = cv2.medianBlur(img, 3)
    return img


def compute_completion_percentage(
    session,
    reference_img,
    canvas_size,
    stroke_width=3,
    weights=None,
    max_orb_matches=200,
    include_sift=False,
):
    """
    Computes a completion percentage against a reference image using multiple
    comparison methods. Returns a dict of all scores and a 0-100 percentage.
    """
    if canvas_size is None:
        raise ValueError("canvas_size must be specified and match the Pulsekey app canvas dimensions.")

    extractor = StaticFeatureExtractor(session, canvas_size=canvas_size, stroke_width=stroke_width)
    user_img = extractor.rasterize()

    ref_bin = _preprocess_binary(reference_img)
    user_bin = _preprocess_binary(user_img)

    if ref_bin is None or user_bin is None:
        raise ValueError("reference_img and user drawing must be valid images")

    ssim_score = extractor.compare_ssim(user_bin, ref_bin)
    orb_matches = extractor.compare_orb(user_bin, ref_bin)
    contour_distance = extractor.compare_contour(user_bin, ref_bin)

    orb_score_norm = 0.0
    if max_orb_matches > 0:
        orb_score_norm = min(orb_matches / max_orb_matches, 1.0)

    contour_similarity = 0.0
    if contour_distance is not None:
        contour_similarity = 1.0 / (1.0 + contour_distance)

    sift_matches = None
    sift_score_norm = None
    if include_sift:
        try:
            sift_matches = extractor.compare_sift(user_bin, ref_bin)
            sift_score_norm = min(sift_matches / max_orb_matches, 1.0)
        except ImportError:
            sift_matches = None
            sift_score_norm = None

    default_weights = {"ssim": 0.4, "orb": 0.3, "contour": 0.3}
    if include_sift and sift_score_norm is not None:
        default_weights = {"ssim": 0.35, "orb": 0.25, "contour": 0.25, "sift": 0.15}
    if weights:
        default_weights.update(weights)

    completion_percentage = (
        default_weights.get("ssim", 0.0) * ssim_score
        + default_weights.get("orb", 0.0) * orb_score_norm
        + default_weights.get("contour", 0.0) * contour_similarity
        + default_weights.get("sift", 0.0) * (sift_score_norm or 0.0)
    ) * 100

    return {
        "ssim_score": ssim_score,
        "orb_matches": orb_matches,
        "orb_score_norm": orb_score_norm,
        "contour_distance": contour_distance,
        "contour_similarity": contour_similarity,
        "sift_matches": sift_matches,
        "sift_score_norm": sift_score_norm,
        "completion_percentage": completion_percentage,
        "weights": default_weights,
    }


def extract_static_features_batch(sessions, canvas_size, stroke_width=3, validate=False):
    results = []
    validator = StaticSessionValidator(require_canvas_size=True)
    for session in sessions:
        if validate:
            report = validator.validate(session, canvas_size=canvas_size)
            if not report["is_valid"]:
                results.append({"sessionId": session.get("sessionId"), "errors": report["errors"]})
                continue
        extractor = StaticFeatureExtractor(session, canvas_size=canvas_size, stroke_width=stroke_width)
        features = extractor.extract_all_features()
        features["sessionId"] = session.get("sessionId")
        results.append(features)
    return results


def features_to_dataframe(features_list):
    if not features_list:
        return pd.DataFrame()
    return pd.DataFrame(features_list)


class StaticFeatureExtractor:
    def __init__(self, session, canvas_size, stroke_width=3):
        self.session = session
        self.canvas_size = canvas_size
        self.stroke_width = stroke_width
        self.strokes = session.get("strokes", [])
        self.points = [pt for stroke in self.strokes for pt in stroke.get("points", [])]
        self._infer_canvas_size()

    def _infer_canvas_size(self):
        if not self.canvas_size:
            raise ValueError("canvas_size must be specified and match the Pulsekey app canvas dimensions.")

    def rasterize(self):
        img = np.zeros(self.canvas_size[::-1], dtype=np.uint8)
        for stroke in self.strokes:
            pts = np.array([[pt["x"], pt["y"]] for pt in stroke.get("points", [])], dtype=np.int32)
            if len(pts) > 1:
                cv2.polylines(img, [pts], isClosed=False, color=255, thickness=self.stroke_width)
        return img

    def compare_sift(self, user_img, ref_img):
        """
        Compare two images using SIFT feature matching (affine-invariant).
        Returns number of good matches (int).
        """
        try:
            sift = cv2.SIFT_create()
        except AttributeError:
            raise ImportError("SIFT is not available. Please install opencv-contrib-python.")
        kp1, des1 = sift.detectAndCompute(user_img, None)
        kp2, des2 = sift.detectAndCompute(ref_img, None)
        if des1 is None or des2 is None:
            return 0
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]
        return len(good_matches)

    def compare_ssim(self, user_img, ref_img):
        """
        Compare two images using Structural Similarity Index (SSIM).
        Returns SSIM score (float, 0-1).
        """
        if user_img.shape != ref_img.shape:
            user_img = cv2.resize(user_img, (ref_img.shape[1], ref_img.shape[0]), interpolation=cv2.INTER_NEAREST)
        user_img = user_img.astype(np.uint8)
        ref_img = ref_img.astype(np.uint8)
        score = ssim(user_img, ref_img)
        return score

    def compare_orb(self, user_img, ref_img):
        """
        Compare two images using ORB feature matching.
        Returns number of good matches.
        """
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(user_img, None)
        kp2, des2 = orb.detectAndCompute(ref_img, None)
        if des1 is None or des2 is None:
            return 0
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = [m for m in matches if m.distance < 50]
        return len(good_matches)

    def compare_contour(self, user_img, ref_img):
        """
        Compare two images using contour matching (shape similarity).
        Returns shape similarity score (lower is more similar).
        """
        contours1, _ = cv2.findContours(user_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(ref_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours1 or not contours2:
            return None
        cnt1 = max(contours1, key=cv2.contourArea)
        cnt2 = max(contours2, key=cv2.contourArea)
        score = cv2.matchShapes(cnt1, cnt2, cv2.CONTOURS_MATCH_I1, 0.0)
        return score

    def bounding_box_area(self):
        xs = [pt["x"] for pt in self.points]
        ys = [pt["y"] for pt in self.points]
        if not xs or not ys:
            return np.nan
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return (max_x - min_x) * (max_y - min_y)

    def stroke_length_stats(self):
        lengths = []
        for stroke in self.strokes:
            pts = stroke.get("points", [])
            if len(pts) < 2:
                lengths.append(0)
                continue
            l = sum(
                np.linalg.norm(
                    np.array([pts[i]["x"], pts[i]["y"]])
                    - np.array([pts[i - 1]["x"], pts[i - 1]["y"]])
                )
                for i in range(1, len(pts))
            )
            lengths.append(l)
        return {
            "total_stroke_length": np.sum(lengths),
            "mean_stroke_length": np.mean(lengths) if lengths else np.nan,
            "max_stroke_length": np.max(lengths) if lengths else np.nan,
            "min_stroke_length": np.min(lengths) if lengths else np.nan,
            "stroke_count": len(lengths),
            "stroke_length_variance": np.var(lengths) if lengths else np.nan,
        }

    def stroke_orientation_distribution(self, bins=8):
        angles = []
        for stroke in self.strokes:
            pts = stroke.get("points", [])
            for i in range(1, len(pts)):
                dx = pts[i]["x"] - pts[i - 1]["x"]
                dy = pts[i]["y"] - pts[i - 1]["y"]
                angle = np.arctan2(dy, dx)
                angles.append(angle)
        if not angles:
            return {"stroke_orientation_histogram": np.zeros(bins)}
        hist, _ = np.histogram(angles, bins=bins, range=(-np.pi, np.pi))
        return {"stroke_orientation_histogram": hist}

    def center_of_mass_offset(self):
        if not self.points:
            return {"center_of_mass_offset": np.nan}
        xs = [pt["x"] for pt in self.points]
        ys = [pt["y"] for pt in self.points]
        centroid = (np.mean(xs), np.mean(ys))
        canvas_center = (self.canvas_size[0]/2, self.canvas_size[1]/2)
        offset = np.linalg.norm(np.array(centroid) - np.array(canvas_center))
        return {"center_of_mass_offset": offset}

    def quadrant_occupancy(self):
        if not self.points:
            return {"quadrant_occupancy": [0, 0, 0, 0]}
        w, h = self.canvas_size
        counts = [0,0,0,0]
        for pt in self.points:
            x, y = pt["x"], pt["y"]
            if x < w/2 and y < h/2:
                counts[0] += 1  # Top-left
            elif x >= w/2 and y < h/2:
                counts[1] += 1  # Top-right
            elif x < w/2 and y >= h/2:
                counts[2] += 1  # Bottom-left
            else:
                counts[3] += 1  # Bottom-right
        total = sum(counts)
        occupancy = [c/total if total else 0 for c in counts]
        return {"quadrant_occupancy": occupancy}

    def perimeter_to_area_ratio(self):
        hull_feats = self.convex_hull_features()
        area = hull_feats.get("convex_hull_area", np.nan)
        perimeter = hull_feats.get("convex_hull_perimeter", np.nan)
        if area and area > 0:
            ratio = perimeter / area
        else:
            ratio = np.nan
        return {"perimeter_to_area_ratio": ratio}

    def convex_hull_efficiency(self):
        hull_feats = self.convex_hull_features()
        area = hull_feats.get("convex_hull_area", np.nan)
        drawing_area = self.drawing_area()
        if area and area > 0:
            efficiency = drawing_area / area
        else:
            efficiency = np.nan
        return {"convex_hull_efficiency": efficiency}

    def self_intersection_count(self):
        # Simple approach: count intersections between all stroke segments
        segments = []
        for stroke in self.strokes:
            pts = stroke.get("points", [])
            for i in range(1, len(pts)):
                segments.append(((pts[i - 1]["x"], pts[i - 1]["y"]), (pts[i]["x"], pts[i]["y"])))
        def ccw(A,B,C):
            return (C[1]-A[1])*(B[0]-A[0]) > (B[1]-A[1])*(C[0]-A[0])
        def intersect(A,B,C,D):
            return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
        count = 0
        for i in range(len(segments)):
            for j in range(i+1, len(segments)):
                A,B = segments[i]
                C,D = segments[j]
                if intersect(A,B,C,D):
                    count += 1
        return {"self_intersection_count": count}

    def left_right_balance_index(self):
        if not self.points:
            return {"left_right_balance_index": np.nan}
        w = self.canvas_size[0]
        left = sum(1 for pt in self.points if pt["x"] < w / 2)
        right = sum(1 for pt in self.points if pt["x"] >= w / 2)
        total = left + right
        if total == 0:
            return {"left_right_balance_index": np.nan}
        return {"left_right_balance_index": abs(left - right) / total}

    def top_bottom_balance_index(self):
        if not self.points:
            return {"top_bottom_balance_index": np.nan}
        h = self.canvas_size[1]
        top = sum(1 for pt in self.points if pt["y"] < h / 2)
        bottom = sum(1 for pt in self.points if pt["y"] >= h / 2)
        total = top + bottom
        if total == 0:
            return {"top_bottom_balance_index": np.nan}
        return {"top_bottom_balance_index": abs(top - bottom) / total}

    def grid_alignment_score(self, grid_size=10):
        if not self.points:
            return {"grid_alignment_score": np.nan}
        aligned = 0
        for pt in self.points:
            if pt["x"] % grid_size == 0 or pt["y"] % grid_size == 0:
                aligned += 1
        score = aligned / len(self.points) if self.points else np.nan
        return {"grid_alignment_score": score}

    def stroke_connectivity_ratio(self):
        # Count strokes that are connected (end of one is start of next)
        connected = 0
        for i in range(1, len(self.strokes)):
            prev_pts = self.strokes[i - 1].get("points", [])
            curr_pts = self.strokes[i].get("points", [])
            if prev_pts and curr_pts:
                if prev_pts[-1]["x"] == curr_pts[0]["x"] and prev_pts[-1]["y"] == curr_pts[0]["y"]:
                    connected += 1
        ratio = connected / len(self.strokes) if self.strokes else np.nan
        return {"stroke_connectivity_ratio": ratio}

    def mean_inter_stroke_distance(self):
        # Mean distance between endpoints of consecutive strokes
        if len(self.strokes) < 2:
            return {"mean_inter_stroke_distance": np.nan}
        distances = []
        for i in range(1, len(self.strokes)):
            prev_pts = self.strokes[i - 1].get("points", [])
            curr_pts = self.strokes[i].get("points", [])
            if prev_pts and curr_pts:
                dist = np.linalg.norm(
                    np.array([prev_pts[-1]["x"], prev_pts[-1]["y"]])
                    - np.array([curr_pts[0]["x"], curr_pts[0]["y"]])
                )
                distances.append(dist)
        mean_dist = np.mean(distances) if distances else np.nan
        return {"mean_inter_stroke_distance": mean_dist}

    def drawing_area(self):
        img = self.rasterize()
        return np.count_nonzero(img)

    def convex_hull_features(self):
        pts = np.array([[pt["x"], pt["y"]] for pt in self.points], dtype=np.int32)
        if len(pts) < 3:
            return {"convex_hull_area": np.nan, "convex_hull_perimeter": np.nan}
        hull = cv2.convexHull(pts)
        area = cv2.contourArea(hull)
        perimeter = cv2.arcLength(hull, True)
        return {"convex_hull_area": area, "convex_hull_perimeter": perimeter}

    def hu_moments(self):
        img = self.rasterize()
        moments = cv2.moments(img)
        hu = cv2.HuMoments(moments).flatten()
        return {f"hu_moment_{i+1}": float(h) for i, h in enumerate(hu)}

    def symmetry(self):
        img = self.rasterize()
        vert = np.fliplr(img)
        horiz = np.flipud(img)
        vert_corr = np.corrcoef(img.flatten(), vert.flatten())[0,1]
        horiz_corr = np.corrcoef(img.flatten(), horiz.flatten())[0,1]
        return {"vertical_symmetry": vert_corr, "horizontal_symmetry": horiz_corr}

    def extract_all_features(self):
        features = {}
        features["static_bounding_box_area"] = self.bounding_box_area()
        features["static_drawing_area"] = self.drawing_area()
        # Percentage of canvas area covered
        total_canvas_area = self.canvas_size[0] * self.canvas_size[1] if self.canvas_size else np.nan
        if total_canvas_area and total_canvas_area > 0:
            percent_covered = 100.0 * features['static_drawing_area'] / total_canvas_area
        else:
            percent_covered = np.nan
        features["static_percent_canvas_covered"] = percent_covered
        features.update(self.stroke_length_stats())
        features.update(self.convex_hull_features())
        features.update(self.hu_moments())
        features.update(self.symmetry())
        features.update(self.stroke_orientation_distribution())
        features.update(self.center_of_mass_offset())
        features.update(self.quadrant_occupancy())
        features.update(self.perimeter_to_area_ratio())
        features.update(self.convex_hull_efficiency())
        features.update(self.self_intersection_count())
        features.update(self.left_right_balance_index())
        features.update(self.top_bottom_balance_index())
        features.update(self.grid_alignment_score())
        features.update(self.stroke_connectivity_ratio())
        features.update(self.mean_inter_stroke_distance())
        return features

# Example usage
if __name__ == "__main__":
    session = {
        "sessionId": "example-001",
        "strokes": [
            {"strokeId": "s1", "points": [{"x": 10, "y": 10}, {"x": 50, "y": 50}, {"x": 90, "y": 10}]}
        ],
    }
    canvas_size = (200, 200)
    extractor = StaticFeatureExtractor(session, canvas_size=canvas_size)
    features = extractor.extract_all_features()
    print(features)
    if "static_percent_canvas_covered" in features:
        print(f"Percent of canvas covered: {features['static_percent_canvas_covered']:.2f}%")

    ref_img = np.zeros(extractor.canvas_size[::-1], dtype=np.uint8)
    cv2.rectangle(ref_img, (10, 10), (90, 50), 255, thickness=-1)
    completion = compute_completion_percentage(session, ref_img, canvas_size=extractor.canvas_size)
    print(f"Completion vs. reference: {completion['completion_percentage']:.2f}%")
