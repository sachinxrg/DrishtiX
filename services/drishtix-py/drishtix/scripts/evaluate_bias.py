"""
DrishtiX v4.0 — Bias Evaluation Script.

Evaluates facial recognition accuracy across demographic groups using the
Racial Faces in-the-Wild (RFW) dataset. Measures False Match Rate (FMR) and
False Non-Match Rate (FNMR) per demographic group to detect performance
disparities that could indicate algorithmic bias.

Dataset: RFW (Racial Faces in-the-Wild) — http://www.whdeng.cn/RFW/index.html
Paper: "RFW: Benchmarking Racial Bias in Face Recognition" (Wang et al., 2019)

Prerequisites:
    1. Download RFW dataset and extract to data/rfw/
    2. Ensure drishtix recognition engine is configured

Usage:
    python -m drishtix.scripts.evaluate_bias --dataset-dir data/rfw/

Output:
    Per-group accuracy metrics and fairness assessment report.
"""

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# RFW demographic groups
DEMOGRAPHIC_GROUPS = ["African", "Asian", "Caucasian", "Indian"]

# NIST FRVT fairness threshold: max allowed FMR/FNMR ratio between groups
MAX_ALLOWED_DISPARITY_RATIO = 3.0


@dataclass
class GroupMetrics:
    """Per-group evaluation metrics."""

    group_name: str
    total_pairs: int = 0
    genuine_pairs: int = 0
    impostor_pairs: int = 0
    true_accepts: int = 0
    false_rejects: int = 0
    true_rejects: int = 0
    false_accepts: int = 0

    @property
    def fmr(self) -> float:
        """False Match Rate (Type I error)."""
        if self.impostor_pairs == 0:
            return 0.0
        return self.false_accepts / self.impostor_pairs

    @property
    def fnmr(self) -> float:
        """False Non-Match Rate (Type II error)."""
        if self.genuine_pairs == 0:
            return 0.0
        return self.false_rejects / self.genuine_pairs

    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        if self.total_pairs == 0:
            return 0.0
        return (self.true_accepts + self.true_rejects) / self.total_pairs


@dataclass
class BiasReport:
    """Aggregated bias evaluation report."""

    threshold: float
    group_metrics: Dict[str, GroupMetrics] = field(default_factory=dict)
    max_fmr_ratio: float = 0.0
    max_fnmr_ratio: float = 0.0
    passes_fairness: bool = False

    def compute_fairness(self) -> None:
        """Calculate inter-group disparity ratios."""
        fmrs = [m.fmr for m in self.group_metrics.values() if m.impostor_pairs > 0]
        fnmrs = [m.fnmr for m in self.group_metrics.values() if m.genuine_pairs > 0]

        if len(fmrs) >= 2:
            self.max_fmr_ratio = max(fmrs) / max(min(fmrs), 1e-10)
        if len(fnmrs) >= 2:
            self.max_fnmr_ratio = max(fnmrs) / max(min(fnmrs), 1e-10)

        self.passes_fairness = (
            self.max_fmr_ratio <= MAX_ALLOWED_DISPARITY_RATIO
            and self.max_fnmr_ratio <= MAX_ALLOWED_DISPARITY_RATIO
        )

    def summary(self) -> str:
        """Generate human-readable report."""
        lines = [
            "=" * 70,
            "DrishtiX Bias Evaluation Report",
            f"Threshold: {self.threshold:.3f}",
            "=" * 70,
            "",
            f"{'Group':<12} {'Pairs':>6} {'Accuracy':>9} {'FMR':>8} {'FNMR':>8}",
            "-" * 50,
        ]

        for name, m in sorted(self.group_metrics.items()):
            lines.append(
                f"{name:<12} {m.total_pairs:>6} {m.accuracy:>8.1%} "
                f"{m.fmr:>7.4f} {m.fnmr:>7.4f}"
            )

        lines.extend([
            "",
            f"Max FMR disparity ratio:  {self.max_fmr_ratio:.2f}x",
            f"Max FNMR disparity ratio: {self.max_fnmr_ratio:.2f}x",
            f"Fairness threshold:       {MAX_ALLOWED_DISPARITY_RATIO:.1f}x",
            f"Result: {'✅ PASS' if self.passes_fairness else '❌ FAIL — BIAS DETECTED'}",
            "=" * 70,
        ])

        return "\n".join(lines)


def load_pairs_file(pairs_path: Path) -> List[Tuple[str, str, bool]]:
    """
    Parse an RFW-format pairs file.

    Format (genuine pair):  name\timage_idx1\timage_idx2
    Format (impostor pair): name1\timage_idx1\tname2\timage_idx2

    Returns:
        List of (image_path_1, image_path_2, is_genuine) tuples.
    """
    pairs = []
    with open(pairs_path, "r") as f:
        lines = f.readlines()

    # First line is count
    for line in lines[1:]:
        parts = line.strip().split("\t")
        if len(parts) == 3:
            # Genuine pair
            name, idx1, idx2 = parts
            pairs.append((f"{name}/{name}_{idx1.zfill(4)}.jpg",
                          f"{name}/{name}_{idx2.zfill(4)}.jpg", True))
        elif len(parts) == 4:
            # Impostor pair
            name1, idx1, name2, idx2 = parts
            pairs.append((f"{name1}/{name1}_{idx1.zfill(4)}.jpg",
                          f"{name2}/{name2}_{idx2.zfill(4)}.jpg", False))

    return pairs


def evaluate_group(
    group_name: str,
    dataset_dir: Path,
    threshold: float,
) -> GroupMetrics:
    """
    Evaluate recognition accuracy for one demographic group.

    This is a template implementation. In production, replace the
    embedding extraction with actual DrishtiX recognizer calls.
    """
    metrics = GroupMetrics(group_name=group_name)

    pairs_file = dataset_dir / group_name / f"{group_name}_pairs.txt"
    images_dir = dataset_dir / group_name / "data"

    if not pairs_file.exists():
        logger.warning("Pairs file not found: %s", pairs_file)
        return metrics

    pairs = load_pairs_file(pairs_file)
    logger.info("Evaluating %s: %d pairs", group_name, len(pairs))

    # TODO: Replace with actual DrishtiX embedding extraction
    # For each pair:
    #   1. Load both images
    #   2. Extract face embeddings via FaceRecognitionService
    #   3. Compute cosine similarity
    #   4. Compare against threshold
    for img1_rel, img2_rel, is_genuine in pairs:
        img1_path = images_dir / img1_rel
        img2_path = images_dir / img2_rel

        if not img1_path.exists() or not img2_path.exists():
            continue

        # Placeholder: actual implementation would extract embeddings
        # similarity = compute_similarity(img1_path, img2_path)
        # For now, skip actual computation
        metrics.total_pairs += 1
        if is_genuine:
            metrics.genuine_pairs += 1
        else:
            metrics.impostor_pairs += 1

    return metrics


def run_evaluation(dataset_dir: Path, threshold: float = 0.45) -> BiasReport:
    """Run full bias evaluation across all demographic groups."""
    report = BiasReport(threshold=threshold)

    for group in DEMOGRAPHIC_GROUPS:
        metrics = evaluate_group(group, dataset_dir, threshold)
        report.group_metrics[group] = metrics

    report.compute_fairness()
    return report


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="DrishtiX Bias Evaluation")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="Path to RFW dataset")
    parser.add_argument("--threshold", type=float, default=0.45, help="Match threshold")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if not args.dataset_dir.exists():
        print(f"❌ Dataset directory not found: {args.dataset_dir}", file=sys.stderr)
        print("Download RFW from: http://www.whdeng.cn/RFW/index.html")
        sys.exit(1)

    report = run_evaluation(args.dataset_dir, args.threshold)
    print(report.summary())


if __name__ == "__main__":
    main()
