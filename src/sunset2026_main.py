# src/sunset2026_main.py

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Tuple, List, Callable, Optional
import io
from contextlib import redirect_stdout

from src.location_selector import choose_location_interactive
from src.mesh_builder import build_narrow_mesh
from src.open_meteo_client import get_sunset_utc, get_cloud_profile_option_a
from src.config import (
    MESH_STEP_KM,
    MESH_MAX_DISTANCE_KM,
    PERP_OFFSET_DEFAULT_KM,
)

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
    Returns (avg_low, avg_mid, avg_high, total_n). If no data, total_n = 0.
    """
    total_n = 0
    sum_low = 0.0
    sum_mid = 0.0
    sum_high = 0.0

    for (group, subgroup), entry in stats.items():
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
    verbose: bool = True
):
    """
    Core analysis pipeline that prints via `printer`.
    Used by both CLI main() and Streamlit wrapper.
    """

    # 0. Mark fetch time
    fetch_time_utc = datetime.now(timezone.utc)
    printer(f"\nForecast data fetched at (UTC): {fetch_time_utc.isoformat()}")

    printer(f"\nLocation: ({lat:.6f}, {lon:.6f})")
    printer(f"Azimuth: {azimuth_deg:.1f}°")

    printer(f"\nUsing date: {target_date.isoformat()}")

    # 1. Get sunset UTC
    sunset_utc = get_sunset_utc(lat, lon, target_date)
    printer(f"Sunset UTC: {sunset_utc.isoformat()}")

    # 2. Time windows
    t_before = sunset_utc - timedelta(hours=1)
    t_at = sunset_utc
    t_after = sunset_utc + timedelta(hours=1)

    printer("\nTime window (UTC):")
    printer(f"  Before: {t_before.isoformat()}")
    printer(f"  At:     {t_at.isoformat()}")
    printer(f"  After:  {t_after.isoformat()}")

    # 3. Overhead cloud profile
    printer("\nFetching overhead (local) cloud profile at sunset...")
    overhead_cloud = get_cloud_profile_option_a(lat, lon, t_before, t_at, t_after)

    printer("Overhead cloud profile (%, low/mid/high):")
    printer(
        f"  Before: low={overhead_cloud['low_before']:5.1f}  "
        f"mid={overhead_cloud['mid_before']:5.1f}  "
        f"high={overhead_cloud['high_before']:5.1f}"
    )
    printer(
        f"  At:     low={overhead_cloud['low_at']:5.1f}  "
        f"mid={overhead_cloud['mid_at']:5.1f}  "
        f"high={overhead_cloud['high_at']:5.1f}"
    )
    printer(
        f"  After:  low={overhead_cloud['low_after']:5.1f}  "
        f"mid={overhead_cloud['mid_after']:5.1f}  "
        f"high={overhead_cloud['high_after']:5.1f}"
    )

    # 4. Mesh config
    printer("\nMesh configuration:")
    printer(f"  Step along azimuth:          {MESH_STEP_KM} km")
    printer(f"  Max distance along azimuth:  {MESH_MAX_DISTANCE_KM} km")
    printer(f"  Base perpendicular width B: ±{PERP_OFFSET_DEFAULT_KM} km")

    # 5. Build mesh
    mesh_points = build_narrow_mesh(
        start_lat=lat,
        start_lon=lon,
        azimuth_deg=azimuth_deg,
    )
    printer(f"\nGenerated {len(mesh_points)} mesh points.")

    # 6. Fetch cloud data for mesh points
    enriched_count = 0
    printer("\nFetching cloud data for mesh points (this may take a bit)...")

    for idx, point in enumerate(mesh_points, start=1):
        plat = point["lat"]
        plon = point["lon"]
        try:
            cloud = get_cloud_profile_option_a(plat, plon, t_before, t_at, t_after)
            point.update(cloud)
            enriched_count += 1
        except Exception as e:
            printer(f"  Warning: failed at point {idx} ({plat:.4f}, {plon:.4f}): {e}")

    printer(f"\nSuccessfully enriched {enriched_count} / {len(mesh_points)} points with cloud data.")

    # 7. Summarize by subgroup
    stats = {}

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

    printer("\nAverage cloud cover at sunset by group/subgroup (%, low/mid/high):")
    if not stats:
        printer("  No stats available (likely all cloud fetches failed).")
    else:
        for (group, subgroup), entry in sorted(stats.items()):
            count = entry["count"]
            avg_low = entry["sum_low_at"] / count if count else 0.0
            avg_mid = entry["sum_mid_at"] / count if count else 0.0
            avg_high = entry["sum_high_at"] / count if count else 0.0

            printer(
                f"  {group} / {subgroup:<18} "
                f"(n={count:2d})  "
                f"low={avg_low:5.1f}  mid={avg_mid:5.1f}  high={avg_high:5.1f}"
            )

    # 8. Educational summaries
    printer("\n------------------------------------------------------------")
    printer("Educational condition summaries (based on tonight's data)")
    printer("------------------------------------------------------------")

    low_at = overhead_cloud["low_at"]
    mid_at = overhead_cloud["mid_at"]
    high_at = overhead_cloud["high_at"]

    h_head, h_lines, h_expl = evaluate_overhead_height(low_at, mid_at, high_at)
    _print_condition_block(printer, "Overhead cloud height (local)", h_head, h_lines, h_expl)

    c_head, c_lines, c_expl = evaluate_overhead_coverage(low_at, mid_at, high_at)
    _print_condition_block(printer, "Overhead coverage % (local)", c_head, c_lines, c_expl)

    # Western band (252–350 km)
    west_low, west_mid, west_high, west_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_West", "GroupB_West"]
    )
    if west_n > 0:
        w_head, w_lines, w_expl = evaluate_western_band(west_low, west_mid, west_high)
        _print_condition_block(printer, "Western band (252–350 km)", w_head, w_lines, w_expl)
    else:
        printer("\nWestern band summary skipped (no mesh data for this band).")

    # Cloud horizon band (350–468 km)
    horiz_low, horiz_mid, horiz_high, horiz_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_CloudHorizon", "GroupB_CloudHorizon"]
    )
    if horiz_n > 0:
        ch_head, ch_lines, ch_expl = evaluate_cloud_horizon(horiz_low, horiz_mid, horiz_high)
        _print_condition_block(printer, "Cloud horizon band (350–468 km)", ch_head, ch_lines, ch_expl)
    else:
        printer("\nCloud horizon summary skipped (no mesh data for this band).")

    # Far west (468–936 km)
    far_low, far_mid, far_high, far_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_FarWest", "GroupB_FarWest"]
    )
    if far_n > 0:
        fw_head, fw_lines, fw_expl = evaluate_far_west(far_low, far_mid, far_high)
        _print_condition_block(printer, "Far West band (468–936 km)", fw_head, fw_lines, fw_expl)
    else:
        printer("\nFar West summary skipped (no mesh data for this band).")

    # 9. Sample points
    printer("\nSample enriched points (first 5 with cloud data):")
    printed = 0
    for p in mesh_points:
        if "mid_at" not in p or "high_at" not in p:
            continue

        printer(
            f"  group={p['group']:<1}  sub={p['subgroup']:<18}  side={p['side']:<6}  "
            f"d_along={p['distance_along_km']:6.1f} km  off={p['offset_perp_km']:6.1f} km  "
            f"lat={p['lat']:.4f}  lon={p['lon']:.4f}  "
            f"mid_at={p['mid_at']:5.1f}%  high_at={p['high_at']:5.1f}%"
        )

        printed += 1
        if printed >= 5:
            break

    if printed == 0:
        printer("  (No points with attached cloud data to show.)")


def run_full_sunset_analysis(
    lat: float,
    lon: float,
    azimuth_deg: float,
    target_date: Optional[date] = None,
    verbose: bool = True
) -> str:
    """
    Non-interactive wrapper for Streamlit.
    Runs the full analysis and returns the full printed report as a string.
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
            verbose=verbose,
        )
    return buffer.getvalue()


def main():
    # Interactive CLI entrypoint (unchanged behavior)
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
        verbose=True
    )


if __name__ == "__main__":
    main()
