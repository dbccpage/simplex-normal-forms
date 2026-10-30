"""CDC application and the extremum and quantile cochains, including dynamic
dyadic bucket-boundary splitting and merging under skewed streams.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import sqlite3
from typing import Any, List, Optional, Tuple


def cochain_add(conn: sqlite3.Connection, region: str, amount: float) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
        (region, amount),
    )
    if cursor.fetchone():
        cursor.execute(
            "UPDATE region_extremum_cochain SET frequency = frequency + 1 "
            "WHERE region = ? AND amount = ?;",
            (region, amount),
        )
        return
    cursor.execute(
        "INSERT INTO region_extremum_cochain (region, amount, frequency) VALUES (?, ?, 1);",
        (region, amount),
    )


def cochain_remove(conn: sqlite3.Connection, region: str, amount: float) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT frequency FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
        (region, amount),
    )
    row = cursor.fetchone()
    if row is None:
        return
    if row["frequency"] <= 1:
        cursor.execute(
            "DELETE FROM region_extremum_cochain WHERE region = ? AND amount = ?;",
            (region, amount),
        )
        return
    cursor.execute(
        "UPDATE region_extremum_cochain SET frequency = frequency - 1 "
        "WHERE region = ? AND amount = ?;",
        (region, amount),
    )


def _allocate_bucket_id(cursor: sqlite3.Cursor, region: str, lower_bound: float, bucket_width: float) -> int:
    """Allocates a deterministic integer bucket_id for a newly inserted interval."""
    default_id = int(math.floor((lower_bound + 1e-12) / bucket_width))
    cursor.execute(
        "SELECT 1 FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
        (region, default_id),
    )
    if cursor.fetchone() is None:
        return default_id
    scaled_id = int(round(lower_bound * 1024.0))
    cursor.execute(
        "SELECT 1 FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
        (region, scaled_id),
    )
    if cursor.fetchone() is None:
        return scaled_id
    cursor.execute(
        "SELECT COALESCE(MAX(bucket_id), 0) + 1 FROM region_quantile_cochain WHERE region = ?;",
        (region,),
    )
    row = cursor.fetchone()
    return int(row[0]) if row is not None else 1


def _find_disjoint_dyadic_interval(
    cursor: sqlite3.Cursor,
    region: str,
    amount: float,
    bucket_width: float,
    min_bucket_width: float = 0.625,
) -> Tuple[float, float]:
    """Finds the maximal dyadic sub-interval of [b*W_0, (b+1)*W_0) containing amount
    that is disjoint from all existing active buckets for region.
    """
    base_idx = int(math.floor(amount / bucket_width))
    low = base_idx * bucket_width
    high = (base_idx + 1) * bucket_width
    cursor.execute(
        """
        SELECT lower_bound, upper_bound
        FROM region_quantile_cochain
        WHERE region = ? AND count > 0 AND lower_bound < ? AND upper_bound > ?;
        """,
        (region, high - 1e-12, low + 1e-12),
    )
    existing = [(float(r["lower_bound"]), float(r["upper_bound"])) for r in cursor.fetchall()]
    while existing and (high - low) / 2.0 >= min_bucket_width - 1e-12:
        overlaps = [
            (b_low, b_high)
            for b_low, b_high in existing
            if b_low < high - 1e-12 and b_high > low + 1e-12
        ]
        if not overlaps:
            break
        mid = 0.5 * (low + high)
        if amount < mid:
            high = mid
        else:
            low = mid
    return low, high


def quantile_cochain_add(
    conn: sqlite3.Connection,
    region: str,
    amount: float,
    bucket_width: float = 10.0,
    min_bucket_width: float = 0.625,
) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT bucket_id, count
        FROM region_quantile_cochain
        WHERE region = ? AND lower_bound <= ? AND ? < upper_bound
        ORDER BY (upper_bound - lower_bound) ASC, bucket_id ASC
        LIMIT 1;
        """,
        (region, amount + 1e-12, amount),
    )
    row = cursor.fetchone()
    if row is not None:
        cursor.execute(
            "UPDATE region_quantile_cochain SET count = count + 1 "
            "WHERE region = ? AND bucket_id = ?;",
            (region, int(row["bucket_id"])),
        )
        return
    lower, upper = _find_disjoint_dyadic_interval(
        cursor, region, amount, bucket_width, min_bucket_width=min_bucket_width
    )
    bucket_id = _allocate_bucket_id(cursor, region, lower, bucket_width)
    cursor.execute(
        "INSERT INTO region_quantile_cochain "
        "(region, bucket_id, lower_bound, upper_bound, count) VALUES (?, ?, ?, ?, 1);",
        (region, bucket_id, lower, upper),
    )


def quantile_cochain_remove(
    conn: sqlite3.Connection,
    region: str,
    amount: float,
    bucket_width: float = 10.0,
) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT bucket_id, count
        FROM region_quantile_cochain
        WHERE region = ? AND lower_bound <= ? AND ? < upper_bound
        ORDER BY (upper_bound - lower_bound) ASC, bucket_id ASC
        LIMIT 1;
        """,
        (region, amount + 1e-12, amount),
    )
    row = cursor.fetchone()
    if row is None:
        bucket_id = int(math.floor(amount / bucket_width))
        cursor.execute(
            "SELECT bucket_id, count FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
            (region, bucket_id),
        )
        row = cursor.fetchone()
    if row is None:
        return
    b_id = int(row["bucket_id"])
    if int(row["count"]) <= 1:
        cursor.execute(
            "DELETE FROM region_quantile_cochain WHERE region = ? AND bucket_id = ?;",
            (region, b_id),
        )
        return
    cursor.execute(
        "UPDATE region_quantile_cochain SET count = count - 1 WHERE region = ? AND bucket_id = ?;",
        (region, b_id),
    )


def _load_region_value_frequencies(
    cursor: sqlite3.Cursor,
    region: str,
) -> List[Tuple[float, int]]:
    """Loads exact value frequencies for region from region_extremum_cochain (or base_sales)."""
    cursor.execute(
        "SELECT amount, frequency FROM region_extremum_cochain WHERE region = ? ORDER BY amount ASC;",
        (region,),
    )
    rows = cursor.fetchall()
    if rows:
        return [(float(r["amount"]), int(r["frequency"])) for r in rows if int(r["frequency"]) > 0]
    cursor.execute(
        "SELECT amount, COUNT(*) AS frequency FROM base_sales WHERE region = ? GROUP BY amount ORDER BY amount ASC;",
        (region,),
    )
    return [(float(r["amount"]), int(r["frequency"])) for r in cursor.fetchall()]


def _count_points_in_half_open_interval(
    points: List[Tuple[float, int]],
    low: float,
    high: float,
) -> int:
    return sum(freq for amt, freq in points if (low - 1e-12) <= amt < (high - 1e-12))


def rebalance_quantile_cochain(
    conn: sqlite3.Connection,
    region: str,
    bucket_width: float = 10.0,
    split_threshold: int = 8,
    merge_threshold: int = 3,
    min_bucket_width: float = 0.625,
) -> dict[str, Any]:
    """Dynamically splits overloaded buckets (count > split_threshold) via dyadic bisection
    down to min_bucket_width and merges under-populated sibling/cousin sub-buckets
    (combined count <= merge_threshold) bottom-up within each base cell.
    """
    if bucket_width <= 0.0 or min_bucket_width <= 0.0 or min_bucket_width > bucket_width + 1e-12:
        raise ValueError(
            f"Invalid bucket_width ({bucket_width}) or min_bucket_width ({min_bucket_width})"
        )
    if split_threshold < 2 or merge_threshold < 0 or merge_threshold >= split_threshold:
        raise ValueError(
            f"Invalid thresholds: merge_threshold ({merge_threshold}) must be in [0, split_threshold ({split_threshold}) - 1]"
        )

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT bucket_id, lower_bound, upper_bound, count
        FROM region_quantile_cochain
        WHERE region = ? AND count > 0
        ORDER BY lower_bound ASC, bucket_id ASC;
        """,
        (region,),
    )
    initial_rows = cursor.fetchall()
    if not initial_rows:
        cursor.execute("DELETE FROM region_quantile_cochain WHERE region = ?;", (region,))
        return {
            "region": region,
            "splits_executed": 0,
            "merges_executed": 0,
            "active_bucket_count": 0,
            "total_mass": 0,
        }

    points = _load_region_value_frequencies(cursor, region)
    splits_executed = 0
    merges_executed = 0

    # Phase 1: Top-down recursive dyadic splitting for buckets with count > split_threshold
    split_buckets: List[List[float | int]] = []
    for row in initial_rows:
        stack: List[Tuple[float, float, int]] = [
            (float(row["lower_bound"]), float(row["upper_bound"]), int(row["count"]))
        ]
        while stack:
            low, high, cnt = stack.pop(0)
            if cnt <= 0:
                continue
            width = high - low
            if cnt > split_threshold and (width / 2.0) >= (min_bucket_width - 1e-12):
                mid = 0.5 * (low + high)
                left_cnt = _count_points_in_half_open_interval(points, low, mid)
                right_cnt = cnt - left_cnt
                splits_executed += 1
                stack.insert(0, (mid, high, right_cnt))
                stack.insert(0, (low, mid, left_cnt))
            else:
                split_buckets.append([low, high, cnt])

    split_buckets.sort(key=lambda b: float(b[0]))

    # Determine max dyadic depth d_max such that bucket_width / 2^d_max >= min_bucket_width
    d_max = 0
    while (bucket_width / (2 ** (d_max + 1))) >= (min_bucket_width - 1e-12) and d_max < 16:
        d_max += 1

    # Phase 2: Bottom-up dyadic sibling/cousin merging within each base cell [b*W_0, (b+1)*W_0)
    by_base_cell: dict[int, List[List[float | int]]] = {}
    for b in split_buckets:
        b_idx = int(math.floor((float(b[0]) + 1e-12) / bucket_width))
        by_base_cell.setdefault(b_idx, []).append(b)

    final_buckets: List[Tuple[float, float, int]] = []
    for b_idx in sorted(by_base_cell.keys()):
        cell_low = b_idx * bucket_width
        cell_buckets = by_base_cell[b_idx]

        for depth in range(d_max - 1, -1, -1):
            parent_width = bucket_width / (2**depth)
            grouped_by_parent: dict[int, List[List[float | int]]] = {}
            for b in cell_buckets:
                p_k = int(math.floor(((float(b[0]) - cell_low) + 1e-12) / parent_width))
                grouped_by_parent.setdefault(p_k, []).append(b)

            next_cell_buckets: List[List[float | int]] = []
            for p_k in sorted(grouped_by_parent.keys()):
                grp = grouped_by_parent[p_k]
                grp_sum = sum(int(x[2]) for x in grp)
                has_narrower_child = any(
                    (float(x[1]) - float(x[0])) < parent_width - 1e-12 for x in grp
                )
                if grp_sum <= merge_threshold and (len(grp) >= 2 or has_narrower_child):
                    p_low = cell_low + p_k * parent_width
                    p_high = p_low + parent_width
                    merges_executed += max(1, len(grp) - 1)
                    next_cell_buckets.append([p_low, p_high, grp_sum])
                else:
                    next_cell_buckets.extend(grp)
            cell_buckets = next_cell_buckets

        for b in cell_buckets:
            if int(b[2]) > 0:
                final_buckets.append((float(b[0]), float(b[1]), int(b[2])))

    final_buckets.sort(key=lambda x: x[0])

    # Rewrite region_quantile_cochain for region with strictly increasing bucket_id
    cursor.execute("DELETE FROM region_quantile_cochain WHERE region = ?;", (region,))
    used_ids: set[int] = set()
    for idx, (low, high, cnt) in enumerate(final_buckets):
        candidate_id = int(round(low * 1024.0))
        if candidate_id in used_ids:
            candidate_id = max(used_ids) + 1
        used_ids.add(candidate_id)
        cursor.execute(
            "INSERT INTO region_quantile_cochain "
            "(region, bucket_id, lower_bound, upper_bound, count) VALUES (?, ?, ?, ?, ?);",
            (region, candidate_id, low, high, cnt),
        )

    return {
        "region": region,
        "splits_executed": splits_executed,
        "merges_executed": merges_executed,
        "active_bucket_count": len(final_buckets),
        "total_mass": sum(x[2] for x in final_buckets),
    }


def verify_quantile_cochain_invariants(
    conn: sqlite3.Connection,
    region: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """Checks structural invariants of region_quantile_cochain:
    1. Mass conservation: sum(bucket.count) == COUNT(*) in base_sales for each region.
    2. Positive counts and non-degenerate intervals (lower_bound < upper_bound, count > 0).
    3. Pairwise disjoint ordered intervals (u_i <= l_{i+1}).
    4. Exact point-to-bucket membership: bucket.count equals the exact count of rows in
       base_sales with lower_bound <= amount < upper_bound.
    """
    cursor = conn.cursor()
    if region is not None:
        regions = [region]
    else:
        cursor.execute(
            "SELECT DISTINCT region FROM base_sales UNION SELECT DISTINCT region FROM region_quantile_cochain;"
        )
        regions = sorted(str(r[0]) for r in cursor.fetchall())

    violations: List[str] = []
    for reg in regions:
        cursor.execute("SELECT amount FROM base_sales WHERE region = ?;", (reg,))
        sales_amounts = [float(r["amount"]) for r in cursor.fetchall()]

        cursor.execute(
            """
            SELECT bucket_id, lower_bound, upper_bound, count
            FROM region_quantile_cochain
            WHERE region = ?
            ORDER BY lower_bound ASC, bucket_id ASC;
            """,
            (reg,),
        )
        buckets = cursor.fetchall()
        bucket_mass = sum(int(b["count"]) for b in buckets)
        if bucket_mass != len(sales_amounts):
            violations.append(
                f"Region '{reg}' mass mismatch: quantile cochain sum={bucket_mass} != base_sales count={len(sales_amounts)}"
            )

        prev_high: Optional[float] = None
        for b in buckets:
            b_id = int(b["bucket_id"])
            low = float(b["lower_bound"])
            high = float(b["upper_bound"])
            cnt = int(b["count"])
            if cnt <= 0:
                violations.append(f"Region '{reg}' bucket {b_id} has non-positive count {cnt}")
            if high <= low + 1e-12:
                violations.append(
                    f"Region '{reg}' bucket {b_id} has degenerate interval [{low}, {high})"
                )
            if prev_high is not None and low < prev_high - 1e-12:
                violations.append(
                    f"Region '{reg}' bucket {b_id} [{low}, {high}) overlaps previous upper_bound {prev_high}"
                )
            prev_high = high

            actual_in_bucket = sum(1 for a in sales_amounts if (low - 1e-12) <= a < (high - 1e-12))
            if actual_in_bucket != cnt:
                violations.append(
                    f"Region '{reg}' bucket {b_id} [{low}, {high}) count={cnt} != actual base_sales rows={actual_in_bucket}"
                )

    return len(violations) == 0, violations


def estimate_quantile(
    conn: sqlite3.Connection,
    region: str,
    q: float = 0.5,
) -> Optional[float]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT bucket_id, lower_bound, upper_bound, count
        FROM region_quantile_cochain
        WHERE region = ? AND count > 0
        ORDER BY lower_bound ASC, bucket_id ASC;
        """,
        (region,),
    )
    buckets = cursor.fetchall()
    if not buckets:
        return None
    total_count = sum(bucket["count"] for bucket in buckets)
    if total_count == 0:
        return None
    target_rank = q * total_count
    cumulative = 0
    for bucket in buckets:
        count = bucket["count"]
        if cumulative + count >= target_rank:
            fraction = (target_rank - cumulative) / count if count > 0 else 0.0
            return bucket["lower_bound"] + fraction * (
                bucket["upper_bound"] - bucket["lower_bound"]
            )
        cumulative += count
    return buckets[-1]["upper_bound"]


def compute_true_median(conn: sqlite3.Connection, region: str) -> Optional[float]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT amount FROM base_sales WHERE region = ? ORDER BY amount ASC;",
        (region,),
    )
    rows = cursor.fetchall()
    if not rows:
        return None
    count = len(rows)
    if count % 2 == 1:
        return float(rows[count // 2]["amount"])
    return float(rows[count // 2 - 1]["amount"] + rows[count // 2]["amount"]) / 2.0


def apply_sales_cdc(
    conn: sqlite3.Connection,
    op_type: str,
    sale_id: int,
    old_region: Optional[str] = None,
    new_region: Optional[str] = None,
    old_amount: Optional[float] = None,
    new_amount: Optional[float] = None,
    maintain_cochain: bool = True,
    dynamic_buckets: bool = False,
    bucket_width: float = 10.0,
    split_threshold: int = 8,
    merge_threshold: int = 3,
    min_bucket_width: float = 0.625,
) -> dict[str, int]:
    cursor = conn.cursor()
    if op_type in ("UPDATE", "DELETE") and (old_region is None or old_amount is None):
        cursor.execute("SELECT region, amount FROM base_sales WHERE sale_id = ?;", (sale_id,))
        row = cursor.fetchone()
        if row:
            if old_region is None:
                old_region = row["region"]
            if old_amount is None:
                old_amount = row["amount"]
    affected_regions: set[str] = set()
    if op_type == "INSERT":
        cursor.execute(
            "INSERT INTO base_sales VALUES (?, ?, ?);",
            (sale_id, new_region, new_amount),
        )
        if maintain_cochain and new_region is not None and new_amount is not None:
            cochain_add(conn, new_region, new_amount)
            quantile_cochain_add(
                conn,
                new_region,
                new_amount,
                bucket_width=bucket_width,
                min_bucket_width=min_bucket_width,
            )
            affected_regions.add(new_region)
    elif op_type == "DELETE":
        cursor.execute("DELETE FROM base_sales WHERE sale_id = ?;", (sale_id,))
        if maintain_cochain and old_region is not None and old_amount is not None:
            cochain_remove(conn, old_region, old_amount)
            quantile_cochain_remove(conn, old_region, old_amount, bucket_width=bucket_width)
            affected_regions.add(old_region)
    elif op_type == "UPDATE":
        cursor.execute(
            "UPDATE base_sales SET region = ?, amount = ? WHERE sale_id = ?;",
            (new_region, new_amount, sale_id),
        )
        if maintain_cochain:
            if old_region is not None and old_amount is not None:
                cochain_remove(conn, old_region, old_amount)
                quantile_cochain_remove(conn, old_region, old_amount, bucket_width=bucket_width)
                affected_regions.add(old_region)
            if new_region is not None and new_amount is not None:
                cochain_add(conn, new_region, new_amount)
                quantile_cochain_add(
                    conn,
                    new_region,
                    new_amount,
                    bucket_width=bucket_width,
                    min_bucket_width=min_bucket_width,
                )
                affected_regions.add(new_region)

    splits_total = 0
    merges_total = 0
    if maintain_cochain and dynamic_buckets:
        for reg in sorted(affected_regions):
            reb = rebalance_quantile_cochain(
                conn,
                reg,
                bucket_width=bucket_width,
                split_threshold=split_threshold,
                merge_threshold=merge_threshold,
                min_bucket_width=min_bucket_width,
            )
            splits_total += int(reb["splits_executed"])
            merges_total += int(reb["merges_executed"])

    cursor.execute(
        """
        INSERT INTO sales_cdc_log (
            op_type, sale_id, old_region, new_region, old_amount, new_amount, processed
        ) VALUES (?, ?, ?, ?, ?, ?, 0);
        """,
        (op_type, sale_id, old_region, new_region, old_amount, new_amount),
    )
    conn.commit()
    return {"splits_executed": splits_total, "merges_executed": merges_total}
