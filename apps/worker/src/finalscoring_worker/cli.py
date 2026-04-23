import typer

app = typer.Typer(help="Final Scoring worker CLI")


@app.command()
def ping() -> None:
    print("pong")


@app.command()
def version() -> None:
    print("0.1.0")


if __name__ == "__main__":
    app()
