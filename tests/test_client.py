import os
from pytest import fixture, raises
from minimono import Client

token = os.environ["MONO_TOKEN"]

common_client_instance = Client(token, avoid_ratelimiting=False)

# @fixture
# def client_instance():
    # return Client(token, avoid_ratelimiting=True)


def test_instaniation():
    c1 = common_client_instance
    c1.getStatement(c1['black'])
    c1.saveFile()
    
    filename = f"{c1.user.clientId}.json"
    c2 = Client(token, load_file=filename)
    assert 'a' != c1
    assert c1 == c1 == c2

def test_rates():
    assert common_client_instance.getRates()

def test_get_item_raise():
    with raises(KeyError):
        common_client_instance['']