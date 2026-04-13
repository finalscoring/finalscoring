import typer

app = typer.Typer(help="Final Scoring worker CLI")


@app.command()
def ping() -> None:
    print("pong")


if __name__ == "__main__":
    app()
