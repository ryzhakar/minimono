from email.policy import default
from typing import Optional
from typer import Typer
from os import environ as ENV_VARIABLES
from devtools import debug
from minimono import Client

token = ENV_VARIABLES.get("MONO_TOKEN")

app = Typer()

@app.command('user')
def show_info(filename: Optional[str] = None):
    if not token:
        raise ValueError("$MONO_TOKEN environment variable is expected.")
    
    try:
        cli = Client(token, load_file=str(filename))
    except FileNotFoundError:
        cli = Client(token)
        default_filename = f"{cli.user.clientId}.json"
        try:
            cli.loadFile(default_filename)
        except FileNotFoundError as e:
            if filename:
                raise e
        else:
            if filename:
                filename=default_filename
                print(f"File wasn't found. Loaded the default file {default_filename}")

    
    debug(cli.user)
    cli.saveFile(filename)

def main():
    app()