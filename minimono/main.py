import typer
from devtools import debug
from minimono import Client

app = typer.Typer()

@app.command('user')
def show_info(token: str):
    debug(Client(token).user)

def main():
    app()