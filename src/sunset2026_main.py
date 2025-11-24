# src/sunset2026_main.py

from datetime import date, datetime, timedelta, timezone
from typing import Dict, Tuple, List

from location_selector import choose_location_interactive
from mesh_builder import build_narrow_mesh
from open_meteo_client import get_sunset_utc, get_cloud_profile_option_a
from config import (
    MESH_STEP_KM,
    MESH_MAX_DISTANCE_KM,
    PERP_OFFSET_DEFAULT_KM,
)

from sunset_classification import (
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


def _print_condition_block(title: str, headline: str, detail_lines: List[str], explanation: str):
    print(f"\n{title}")
    print(headline)
    for line in detail_lines:
        print(line)
    print(explanation)


def main():
    # 0. Mark when we fetched forecast data (NOT the model run time)
    fetch_time_utc = datetime.now(timezone.utc)
    print(f"\nForecast data fetched at (UTC): {fetch_time_utc.isoformat()}")

    # 1. Choose location
    loc_name, lat, lon = choose_location_interactive()
    if loc_name is None:
        print("Exiting due to invalid location.")
        return

    print(f"\nLocation: {loc_name} ({lat:.6f}, {lon:.6f})")

    # 2. Ask for azimuth
    try:
        azimuth_str = input(
            "Enter azimuth in degrees (0 = north, 90 = east, 180 = south, 270 = west): "
        )
        azimuth_deg = float(azimuth_str)
    except ValueError:
        print("Invalid azimuth. Exiting.")
        return

    # 3. Choose date (for now, always today; later you can prompt)
    target_date = date.today()
    print(f"\nUsing date: {target_date.isoformat()}")

    # 4. Get sunset time in UTC for this location/date
    try:
        sunset_utc = get_sunset_utc(lat, lon, target_date)
    except Exception as e:
        print(f"Error while fetching sunset time: {e}")
        return

    print(f"Sunset UTC: {sunset_utc.isoformat()}")

    # 5. Define before/at/after times around sunset in UTC
    t_before = sunset_utc - timedelta(hours=1)
    t_at = sunset_utc
    t_after = sunset_utc + timedelta(hours=1)

    print("\nTime window (UTC):")
    print(f"  Before: {t_before.isoformat()}")
    print(f"  At:     {t_at.isoformat()}")
    print(f"  After:  {t_after.isoformat()}")

    # 6. Overhead cloud profile at starting location (Group O concept)
    print("\nFetching overhead (local) cloud profile at sunset...")

    try:
        overhead_cloud = get_cloud_profile_option_a(lat, lon, t_before, t_at, t_after)
        print("Overhead cloud profile (%, low/mid/high):")
        print(
            f"  Before: low={overhead_cloud['low_before']:5.1f}  "
            f"mid={overhead_cloud['mid_before']:5.1f}  "
            f"high={overhead_cloud['high_before']:5.1f}"
        )
        print(
            f"  At:     low={overhead_cloud['low_at']:5.1f}  "
            f"mid={overhead_cloud['mid_at']:5.1f}  "
            f"high={overhead_cloud['high_at']:5.1f}"
        )
        print(
            f"  After:  low={overhead_cloud['low_after']:5.1f}  "
            f"mid={overhead_cloud['mid_after']:5.1f}  "
            f"high={overhead_cloud['high_after']:5.1f}"
        )
    except Exception as e:
        print(f"  Warning: failed to fetch overhead cloud profile: {e}")
        overhead_cloud = None

    # 7. Show mesh configuration (from config.py)
    print("\nMesh configuration:")
    print(f"  Step along azimuth:          {MESH_STEP_KM} km")
    print(f"  Max distance along azimuth:  {MESH_MAX_DISTANCE_KM} km")
    print(f"  Base perpendicular width B: ±{PERP_OFFSET_DEFAULT_KM} km")

    # 8. Build the mesh
    mesh_points = build_narrow_mesh(
        start_lat=lat,
        start_lon=lon,
        azimuth_deg=azimuth_deg,
        # step_km and max_distance_km default from config
        # perpendicular width defaults per band / config
    )

    print(f"\nGenerated {len(mesh_points)} mesh points.")

    # 9. For each mesh point, fetch cloud data around sunset
    enriched_count = 0

    print("\nFetching cloud data for mesh points (this may take a bit)...")

    for idx, point in enumerate(mesh_points, start=1):
        plat = point["lat"]
        plon = point["lon"]

        try:
            cloud = get_cloud_profile_option_a(plat, plon, t_before, t_at, t_after)
            point.update(cloud)
            enriched_count += 1
        except Exception as e:
            # Non-fatal: just warn and continue
            print(f"  Warning: failed at point {idx} ({plat:.4f}, {plon:.4f}): {e}")

    print(f"\nSuccessfully enriched {enriched_count} / {len(mesh_points)} points with cloud data.")

    # 10. Summarize by group/subgroup (e.g., average mid/high at sunset)
    stats = {}  # key: (group, subgroup) -> accum dict

    for p in mesh_points:
        # Only include points that actually have the sunset cloud data
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

    print("\nAverage cloud cover at sunset by group/subgroup (%, low/mid/high):")
    if not stats:
        print("  No stats available (likely all cloud fetches failed).")
    else:
        for (group, subgroup), entry in sorted(stats.items()):
            count = entry["count"]
            avg_low = entry["sum_low_at"] / count if count else 0.0
            avg_mid = entry["sum_mid_at"] / count if count else 0.0
            avg_high = entry["sum_high_at"] / count if count else 0.0

            print(
                f"  {group} / {subgroup:<18} "
                f"(n={count:2d})  "
                f"low={avg_low:5.1f}  mid={avg_mid:5.1f}  high={avg_high:5.1f}"
            )

    # ----------------------------
    # NEW: Educational summaries
    # ----------------------------

    print("\n------------------------------------------------------------")
    print("Educational condition summaries (based on tonight's data)")
    print("------------------------------------------------------------")

    # Overhead conditions
    if overhead_cloud is not None:
        low_at = overhead_cloud["low_at"]
        mid_at = overhead_cloud["mid_at"]
        high_at = overhead_cloud["high_at"]

        h_head, h_lines, h_expl = evaluate_overhead_height(low_at, mid_at, high_at)
        _print_condition_block("Overhead cloud height (local)", h_head, h_lines, h_expl)

        c_head, c_lines, c_expl = evaluate_overhead_coverage(low_at, mid_at, high_at)
        _print_condition_block("Overhead coverage % (local)", c_head, c_lines, c_expl)
    else:
        print("\nOverhead summaries skipped (no overhead data available).")

    # Western band (252–350 km): combine A_West + B_West
    west_low, west_mid, west_high, west_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_West", "GroupB_West"]
    )
    if west_n > 0:
        w_head, w_lines, w_expl = evaluate_western_band(west_low, west_mid, west_high)
        _print_condition_block("Western band (252–350 km)", w_head, w_lines, w_expl)
    else:
        print("\nWestern band summary skipped (no mesh data for this band).")

    # Cloud horizon band (350–468 km): combine A_CloudHorizon + B_CloudHorizon
    horiz_low, horiz_mid, horiz_high, horiz_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_CloudHorizon", "GroupB_CloudHorizon"]
    )
    if horiz_n > 0:
        ch_head, ch_lines, ch_expl = evaluate_cloud_horizon(horiz_low, horiz_mid, horiz_high)
        _print_condition_block("Cloud horizon band (350–468 km)", ch_head, ch_lines, ch_expl)
    else:
        print("\nCloud horizon summary skipped (no mesh data for this band).")

    # Far West band (468–936 km): combine A_FarWest + B_FarWest
    far_low, far_mid, far_high, far_n = _combine_band_averages(
        stats,
        subgroups=["GroupA_FarWest", "GroupB_FarWest"]
    )
    if far_n > 0:
        fw_head, fw_lines, fw_expl = evaluate_far_west(far_low, far_mid, far_high)
        _print_condition_block("Far West band (468–936 km)", fw_head, fw_lines, fw_expl)
    else:
        print("\nFar West summary skipped (no mesh data for this band).")

    # 11. Print a few fully enriched sample points
    print("\nSample enriched points (first 5 with cloud data):")
    printed = 0
    for p in mesh_points:
        if "mid_at" not in p or "high_at" not in p:
            continue

        print(
            f"  group={p['group']:<1}  sub={p['subgroup']:<18}  side={p['side']:<6}  "
            f"d_along={p['distance_along_km']:6.1f} km  off={p['offset_perp_km']:6.1f} km  "
            f"lat={p['lat']:.4f}  lon={p['lon']:.4f}  "
            f"mid_at={p['mid_at']:5.1f}%  high_at={p['high_at']:5.1f}%"
        )

        printed += 1
        if printed >= 5:
            break

    if printed == 0:
        print("  (No points with attached cloud data to show.)")


if __name__ == "__main__":
    main()
