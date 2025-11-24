from datetime import datetime, timedelta, timezone

from open_meteo_client import get_cloud_profile_option_a

def main():
    lat = 42.329516
    lon = -71.036679

    sunset_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    t_before = sunset_utc - timedelta(hours=1)
    t_at = sunset_utc
    t_after = sunset_utc + timedelta(hours=1)

    cloud = get_cloud_profile_option_a(lat, lon, t_before, t_at, t_after)
    print(cloud)

if __name__ == "__main__":
    main()
