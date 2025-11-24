# src/sunset2026_main.py

from datetime import date, timedelta
from typing import Dict, Tuple, List, Callable, Optional
import io
from contextlib import redirect_stdout

from src.location_selector import choose_location_interactive
from src.mesh_builder import build_narrow_mesh
from src.open_meteo_client import get_sunset_utc, get_cloud_profile_option_a

from src.utils_geo import get_timezone_from_coords, format_local_time

from src.sunset_classification import (
    evaluate_far_west,
    evaluate_overhead_height,
    evaluate_overhead_coverage,
    evaluate_western_band,
    evaluate_cloud_horizon,
)


def _combine_band_averages(
    stats: Dict[Tuple[str, str], Dict[str, float]],
    subgroups: List[str]
) -> Tuple[float, float, float, int]:
    """
    Combine low/mid/high_at averages across multiple subgroups, weighted by count.
    Returns (avg_low, avg_mid, avg_high, total_n).
    """
    total_n = 0
    sum_low = 0.0
    sum_mid = 0.0
    sum_high = 0.0

    for (_group, subgroup), entry in stats.items():
        if subgroup not in subgroups:
            continue
        n = int(entry.get("count", 0))
        if n <= 0:
            continue

        total_n += n
        sum_low += entry.get("sum_low_at", 0.0)
        sum_mid += entry.get("sum_mid_at", 0.0)
        sum_high += entry.get("sum_high_at", 0.0)

    if total_n == 0:
        return 0.0, 0.0, 0.0, 0

    return sum_low / total_n, sum_mid / total_n, sum_high / total_n, total_n


def _print_condition_block(
    printer: Callable[[str], None],
    title: str,
    headline: str,
    detail_lines: List[str],
    explanation: str
):
    printer(f"\n{title}")
    printer(headline)
    for line in detail_lines:
        printer(line)
    printer(explanation)


def _run_analysis(
    lat: float,
    lon: float,
    azimuth_deg: float,
    target_date: date,
    printer: Callable[[str], None],
):
    """
    Core analysis pipeline that prints your clean educational report.
    """

    # 1) Sunset time (UTC for analysis)
    sunset_utc = get_sunset_utc(lat, lon, target_date)

    # 2) Local timezone + formatted local sunset for display
    tzname = get_timezone_from_coords(lat, lon)
    sunset_local_str = format_local_time(sunset_utc, tzname)

    # 3) Time window around sunset (UTC)
    t_before = sunset_utc - timedelta(hours=1)
    t_at = sunset_utc
    t_after = sunset_utc + timedelta(hours=1)

    # 4) Overhead cloud profile
    overhead_cloud = get_cloud_profile_option_a(lat, lon, t_before, t_at, t_after)

    # ---------------- CLEAN HEADER ----------------
    printer("📄 Sunset Report\n")
    printer(f"Location: ({lat:.6f}, {lon:.6f})")
    printer(f"Azimuth: {azimuth_deg:.1f}°\n")
    printer(f"Date: {target_date.isoformat()}")
    printer(f"Sunset: {sunset_local_str}")
    printer(f"Sunset UTC: {sunset_utc.isoformat()}\n")

    # 5) Build mesh
    mesh_points = build_narrow_mesh(
        start_lat=lat,
        start_lon=lon,
        azimuth_deg=azimuth_deg,
    )

    # 6) Fetch cloud data for mesh points
    enriched = 0
    total = len(mesh_points)

    for point in mesh_points:
        plat = point["lat"]
        plon = point["lon"]
        try:
            cloud = get_cloud_profile_option_a(plat, plon, t_before, t_at, t_after)
            point.update(cloud)
            enriched += 1
        except Exception:
            # Silent on purpose for clean report
            continue

    printer(f"Successfully enriched {enriched} / {total} points with cloud data.\n")

    printer("------------------------------------------------------------")
    printer("Educational condition summaries (based on tonight's data)")
    printer("------------------------------------------------------------")

    # 7) Per-subgroup stats for band averages
    stats: Dict[Tuple[str, str], Dict[str, float]] = {}

    for p in mesh_points:
        if "mid_at" not in p or "high_at" not in p:
            continue

        key = (p["group"], p["subgroup"])
        entry = stats.get(key)
        if entry is None:
            entry = {
                "count": 0,
                "sum_low_at": 0.0,
                "sum_mid_at": 0.0,
                "sum_high_at": 0.0,
            }
            stats[key] = entry

        entry["count"] += 1
        entry["sum_low_at"] += p.get("low_at", 0.0)
        entry["sum_mid_at"] += p.get("mid_at", 0.0)
        entry["sum_high_at"] += p.get("high_at", 0.0)

    # 8) Overhead evaluations (local)
    low_at = overhead_cloud["low_at"]
    mid_at = overhead_cloud["mid_at"]
    high_at = overhead_cloud["high_at"]

    h_head, h_lines, h_expl = evaluate_overhead_height(low_at, mid_at, high_at)
    _print_condition_block(printer, "Overhead cloud height (local)", h_head, h_lines, h_expl)

    c_head, c_lines, c_expl = evaluate_overhead_coverage(low_at, mid_at, high_at)
    _print_condition_block(printer, "Overhead coverage % (local)", c_head, c_lines, c_expl)

    # 9) Western band (252–350 km)
    west_low, west_mid, west_high, west_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_West", "GroupB_West"]
    )
    if west_n > 0:
        w_head, w_lines, w_expl = evaluate_western_band(west_low, west_mid, west_high)
        _print_condition_block(printer, "Western band (252–350 km)", w_head, w_lines, w_expl)

    # 10) Cloud horizon band (350–468 km)
    horiz_low, horiz_mid, horiz_high, horiz_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_CloudHorizon", "GroupB_CloudHorizon"]
    )
    if horiz_n > 0:
        ch_head, ch_lines, ch_expl = evaluate_cloud_horizon(horiz_low, horiz_mid, horiz_high)
        _print_condition_block(printer, "Cloud horizon band (350–468 km)", ch_head, ch_lines, ch_expl)

    # 11) Far west band (468–936 km)
    far_low, far_mid, far_high, far_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_FarWest", "GroupB_FarWest"]
    )
    if far_n > 0:
        fw_head, fw_lines, fw_expl = evaluate_far_west(far_low, far_mid, far_high)
        _print_condition_block(printer, "Far West band (468–936 km)", fw_head, fw_lines, fw_expl)


def run_full_sunset_analysis(
    lat: float,
    lon: float,
    azimuth_deg: float,
    target_date: Optional[date] = None,
) -> str:
    """
    Streamlit wrapper: runs analysis and returns full report text.
    """
    if target_date is None:
        target_date = date.today()

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        _run_analysis(
            lat=lat,
            lon=lon,
            azimuth_deg=azimuth_deg,
            target_date=target_date,
            printer=print,
        )
    return buffer.getvalue()


def main():
    # CLI entrypoint (still works)
    loc_name, lat, lon = choose_location_interactive()
    if loc_name is None:
        print("Exiting due to invalid location.")
        return

    print(f"\nLocation: {loc_name} ({lat:.6f}, {lon:.6f})")

    try:
        azimuth_str = input(
            "Enter azimuth in degrees (0 = north, 90 = east, 180 = south, 270 = west): "
        )
        azimuth_deg = float(azimuth_str)
    except ValueError:
        print("Invalid azimuth. Exiting.")
        return

    target_date = date.today()
    _run_analysis(
        lat=lat,
        lon=lon,
        azimuth_deg=azimuth_deg,
        target_date=target_date,
        printer=print,
    )


if __name__ == "__main__":
    main()
