# Shares mutable state
# to minimize API calls

from datetime import datetime, timezone
import os
from pytest import fixture, raises
from minimono import Client, TIMEBLOCK, default_timeframe, TimeConstraintError

token = os.environ["MONO_TOKEN"]

common_client_instance = Client(token, avoid_ratelimiting=False)
rate_limited_instance = Client(token, avoid_ratelimiting=True)

# @fixture
# def client_instance():
    # return Client(token, avoid_ratelimiting=True)


def test_client_roundtrip():
    c1 = common_client_instance
    with raises(ValueError):
        c1.getStatement(c1['black'], to_time=datetime.now())

    c1.getStatement(c1['black'], to_time=datetime.now(tz=timezone.utc), from_time=datetime.now(tz=timezone.utc)-TIMEBLOCK)
    c1.saveFile()
    
    filename = f"{c1.user.clientId}.json"
    c2 = Client(token, load_file=filename)
    c3 = Client(token, load_file=filename)
    c3.getStatement(c1['black']) # Should be cached already

    assert 'a' != c1
    assert c1 == c2 == c3

def test_tx_methods():
    tx = list(common_client_instance['black'].cached_statement.values())[0]
    assert tx.next > tx[-1].time
    assert  iter(tx)

def test_rates():
    assert common_client_instance.getRates()

def test_get_item_raise():
    with raises(KeyError):
        common_client_instance['']

def test_timeframe_raises():
    d = datetime(2017, 10, 1, tzinfo=timezone.utc)
    with raises(TimeConstraintError):
        default_timeframe(end_date=d)

def test_ratelimiter():
    rate_limited_instance.getStatement(rate_limited_instance['white'])