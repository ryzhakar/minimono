import os
from pytest import fixture
from minimono import Client

token = os.environ["MONO_TOKEN"]

@fixture
def client_instance():
    return Client(token, avoid_ratelimiting=False)


def test_instaniation(client_instance):
    c1 = client_instance
    c1.getStatement(c1['black'])
    c1.saveFile()
    
    filename = f"{c1.user.clientId}.json"
    c2 = Client(token, load_file=filename)
    assert c1 == c2