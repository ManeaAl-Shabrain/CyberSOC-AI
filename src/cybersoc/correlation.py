from datetime import timedelta

from cybersoc.schemas.events import SecurityEvent, Severity

WINDOW = timedelta(minutes=5)


def correlate(events: list[SecurityEvent]) -> tuple[SecurityEvent, ...]:
    ordered = sorted(events, key=lambda item: (item.timestamp, item.event_id))
    for success in reversed(ordered):
        if success.event_type != "auth_success":
            continue
        failures = tuple(
            item for item in ordered
            if item.asset_id == success.asset_id and item.event_type == "auth_failure"
            and success.timestamp - WINDOW <= item.timestamp < success.timestamp
        )
        if len(failures) >= 3:
            reports = tuple(
                item for item in ordered
                if item.asset_id == success.asset_id and item.event_type == "mfa_fraud_report"
                and success.timestamp <= item.timestamp <= success.timestamp + WINDOW
            )
            return (*failures, success, *reports)
    return ()


def severity_for(cluster: tuple[SecurityEvent, ...], privileged: bool, change: str) -> Severity:
    if not cluster:
        return Severity.low
    if privileged and change == "none":
        return Severity.critical if any(item.event_type == "mfa_fraud_report" for item in cluster) else Severity.high
    return Severity.medium
