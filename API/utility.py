from datetime import datetime, timedelta, timezone
from typing import Sequence, Optional
from .exceptions import TimeConstraintError

TIMEBLOCK = timedelta(days=31)

def align_datetime(date: datetime, step: timedelta) -> datetime:
    """Aligns a datetime to a certain timedelta."""

    aligned_timestamp = date.timestamp() // step.total_seconds() * step.total_seconds()
    return datetime.fromtimestamp(aligned_timestamp, tz=timezone.utc)


def default_timeframe(end_date: Optional[datetime]=None):
    if end_date is None:
        end_date =  datetime.now(tz=timezone.utc)
    to = end_date
    fr = datetime.now(tz=timezone.utc) - timedelta(seconds=2682000.0)

    if datetime(2017, 10, 1) > fr:
        raise TimeConstraintError('The oldest data API can provide is from 2017-10-01')
    
    return fr, to

def construct_bucket_list(
    fr: datetime = datetime(2017, 11, 1, tzinfo=timezone.utc),
    to: datetime = datetime.now(tz=timezone.utc),
    step: timedelta = TIMEBLOCK
    ) -> Sequence[datetime]:
    """Returns a list of bucket daytimes in reversed order."""

    txbucket_keys = list()

    first_bucket_date = align_datetime(fr, step)
    last_bucket_date = align_datetime(to, step)
    txbucket_keys.append(last_bucket_date)

    iterating_bucket_date = last_bucket_date - step
    while iterating_bucket_date >= first_bucket_date:
            txbucket_keys.append(iterating_bucket_date)
            last_bucket_date = iterating_bucket_date
            iterating_bucket_date -= step

    return txbucket_keys
