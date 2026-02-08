import typer
from pie.cli.pipeline import run_full_pipeline

app = typer.Typer(help="Passenger Impact Engine (PIE) CLI")

@app.command()
def refresh(
    config: str = typer.Option("configs/demo.yml", "--config"),
    out: str = typer.Option("/app/out", "--out"),
    audit: str = typer.Option("ledger", "--audit"),
):
    run_full_pipeline(config_path=config, out_dir=out, audit=audit)

if __name__ == "__main__":
    app()
