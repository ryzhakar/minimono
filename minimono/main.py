from typer import Typer
from os import environ as ENV_VARIABLES
from devtools import debug
from minimono import Client

token = ENV_VARIABLES.get("MONO_TOKEN")

app = Typer()

@app.command('user')
def show_info():
    if token:
        cli = Client(token)
        debug(cli.user)
        cli.saveFile()

def main():
    app()