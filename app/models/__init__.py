from zoneinfo import ZoneInfo
from datetime import datetime


class TimezoneMixin:
    def _to_local_time(self, dt_field: datetime) -> datetime | None:
        if not dt_field:
            return None
        utc_tz = ZoneInfo("UTC")
        rome_tz = ZoneInfo("Europe/Rome")
        utc_aware = (
            dt_field.replace(tzinfo=utc_tz) if dt_field.tzinfo is None else dt_field
        )
        return utc_aware.astimezone(rome_tz)
