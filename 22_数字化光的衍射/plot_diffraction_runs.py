#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt


CSV_FILE = Path("Capstone Data.csv")

# Column mapping inferred from header:
# run 1: y=0, x=1
# run 2: y=2, x=3
# run 3: y=4, x=5
# run 4: y=6, x=7
RUN_COLUMN_MAP = {
    1: (1, 0),
    2: (3, 2),
    3: (5, 4),
    4: (7, 6),
}


def to_float(value: str):
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def main() -> None:
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {CSV_FILE}")

    run_data = {run_id: {"x": [], "y": []} for run_id in RUN_COLUMN_MAP}

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)

        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file is empty")

        if len(header) < 8:
            raise ValueError("Unexpected CSV header: expected at least 8 columns")

        print("Detected header columns:")
        for i, name in enumerate(header[:8]):
            print(f"  [{i}] {name}")

        for row in reader:
            if not row:
                continue

            for run_id, (x_idx, y_idx) in RUN_COLUMN_MAP.items():
                if len(row) <= max(x_idx, y_idx):
                    continue

                x = to_float(row[x_idx])
                y = to_float(row[y_idx])

                if x is None or y is None:
                    continue

                run_data[run_id]["x"].append(x)
                run_data[run_id]["y"].append(y)

    for run_id in sorted(run_data.keys()):
        x = run_data[run_id]["x"]
        y = run_data[run_id]["y"]

        if not x:
            print(f"Run #{run_id}: no valid data points, skipped")
            continue

        # Keep data up to 2*x0, where x0 is x at the maximum y.
        max_idx = max(range(len(y)), key=lambda i: y[i])
        x0 = x[max_idx]
        x_limit = 2.0 * x0

        cropped_x = []
        cropped_y = []
        for xi, yi in zip(x, y):
            if xi <= x_limit:
                cropped_x.append(xi)
                cropped_y.append(yi)

        if not cropped_x:
            print(f"Run #{run_id}: no points satisfy x <= 2*x0, skipped")
            continue

        plt.figure(figsize=(8, 5), dpi=150)
        plt.plot(cropped_x, cropped_y, linestyle="-", linewidth=0.8, marker=None)
        plt.xlabel("Position (m)")
        plt.ylabel("Relative Intensity")
        plt.title(f"Diffraction Pattern - Run #{run_id} (x <= 2x0)")
        plt.grid(True, alpha=0.25)
        plt.tight_layout()

        out_name = f"run_{run_id}.png"
        plt.savefig(out_name)
        plt.close()
        print(
            f"Saved: {out_name} (x0={x0:.6g}, x_limit={x_limit:.6g}, points={len(cropped_x)})"
        )


if __name__ == "__main__":
    main()
