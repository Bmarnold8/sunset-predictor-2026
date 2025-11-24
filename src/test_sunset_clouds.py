# src/test_sunset_clouds.py

from datetime import date, timedelta, timezone

from open_meteo_client import get_sunset_utc, get_cloud_profile_option_a


def main():
    # Your home coordinates (example)
    lat = 42.329516
    lon = -71.036679

    # Use today's date; you can change this to any date
    target_date = date.today()

    print(f"Using date: {target_date.isoformat()}")

    # 1. Get sunset time in UTC
    sunset_utc = get_sunset_utc(lat, lon, target_date)
    print(f"Sunset UTC: {sunset_utc.isoformat()}")

    # 2. Define before/at/after times
    t_before = sunset_utc - timedelta(hours=1)
    t_at = sunset_utc
    t_after = sunset_utc + timedelta(hours=1)

    # 3. Get cloud profile around sunset
    cloud = get_cloud_profile_option_a(lat, lon, t_before, t_at, t_after)

    print("\nCloud profile (low/mid/high %):")
    for key, value in cloud.items():
        print(f"  {key:>12}: {value:5.1f}")


if __name__ == "__main__":
    main()
