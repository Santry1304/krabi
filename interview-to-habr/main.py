#!/usr/bin/env python3
"""Interview-to-Habr Pipeline - CLI Interface."""

import click
import os
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import Pipeline
from src.core.gemini_client import GeminiClient
from src.utils.diagnostics import Diagnostics
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Interview → Habr Pipeline: Transform interview transcripts into Habr articles."""
    pass


@cli.command()
def run():
    """Launch interactive TUI interface."""
    try:
        from src.app import InterviewToHabrApp
        app = InterviewToHabrApp()
        app.run()
    except ImportError:
        console.print("[red]TUI not implemented yet. Use CLI commands.[/red]")
        console.print("\nAvailable commands:")
        console.print("  [cyan]python main.py new[/cyan] - Create new project")
        console.print("  [cyan]python main.py process[/cyan] - Process project")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--name", "-n", help="Project name (default: filename)")
@click.option("--model", "-m", default="gemini-2.0-flash-exp", help="Gemini model")
def new(file: str, name: str, model: str):
    """Create new project from input file."""
    try:
        pipeline = Pipeline()

        # Generate project name if not provided
        if not name:
            name = Path(file).stem

        console.print(f"\n[cyan]Creating project:[/cyan] {name}")
        console.print(f"[cyan]Input file:[/cyan] {file}")
        console.print(f"[cyan]Model:[/cyan] {model}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating project...", total=None)

            project_dir = pipeline.create_project(name, Path(file), model)

            progress.update(task, description="[green]Project created!")

        console.print(f"\n[green]✓[/green] Project created: [cyan]{project_dir}[/cyan]")
        console.print(f"\nNext steps:")
        console.print(f"  [cyan]python main.py process {project_dir}[/cyan]")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--from-stage", "-f", type=int, default=2, help="Start from stage (default: 2)")
@click.option("--to-stage", "-t", type=int, default=10, help="End at stage (default: 10)")
@click.option("--materials", "-m", multiple=True, help="Materials to generate (default: all)")
def process(project: str, from_stage: int, to_stage: int, materials: tuple):
    """Process project through pipeline stages."""
    try:
        pipeline = Pipeline()
        pipeline.load_project(Path(project))

        console.print(f"\n[cyan]Processing project:[/cyan] {project}")
        console.print(f"[cyan]Stages:[/cyan] {from_stage} → {to_stage}\n")

        with Progress(console=console) as progress:
            task = progress.add_task(
                f"[cyan]Running stages...",
                total=to_stage - from_stage + 1
            )

            for stage_num in range(from_stage, to_stage + 1):
                # Special handling for stage 9 (select materials)
                kwargs = {}
                if stage_num == 9 and materials:
                    kwargs['selected_materials'] = list(materials)

                progress.update(task, description=f"[cyan]Stage {stage_num}...")

                result = pipeline.run_stage(stage_num, **kwargs)

                if result.success:
                    progress.update(task, advance=1)
                    console.print(f"[green]✓[/green] Stage {stage_num} completed")
                    if result.tokens_used > 0:
                        console.print(f"  Tokens used: {result.tokens_used:,}")
                else:
                    console.print(f"[red]✗[/red] Stage {stage_num} failed: {result.error}")
                    break

        # Show final status
        status = pipeline.get_project_status()
        console.print(f"\n[green]Processing complete![/green]")
        console.print(f"Total tokens: {status['total_tokens']:,}")
        console.print(f"Total API calls: {status['total_calls']}")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("project", type=click.Path(exists=True))
@click.argument("stage", type=int)
def stage(project: str, stage: int):
    """Run specific stage."""
    try:
        pipeline = Pipeline()
        pipeline.load_project(Path(project))

        console.print(f"\n[cyan]Running stage {stage}...[/cyan]\n")

        result = pipeline.run_stage(stage)

        if result.success:
            console.print(f"\n[green]✓[/green] Stage {stage} completed")
            if result.tokens_used > 0:
                console.print(f"Tokens used: {result.tokens_used:,}")
        else:
            console.print(f"\n[red]✗[/red] Stage {stage} failed: {result.error}")
            sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def projects():
    """List all projects."""
    try:
        pipeline = Pipeline()
        project_list = pipeline.list_projects()

        if not project_list:
            console.print("\n[yellow]No projects found.[/yellow]")
            console.print("\nCreate a new project with:")
            console.print("  [cyan]python main.py new <file>[/cyan]\n")
            return

        table = Table(title="Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Stage", justify="right")
        table.add_column("Created")
        table.add_column("Updated")

        for p in project_list:
            table.add_row(
                p["name"],
                f"{p['current_stage']}/10",
                p["created"][:10],
                p["updated"][:10]
            )

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def diagnose():
    """Run system diagnostics."""
    try:
        diag = Diagnostics({})
        results = diag.run_all()

        table = Table(title="System Diagnostics")
        table.add_column("Check")
        table.add_column("Status", justify="center")
        table.add_column("Result")

        for r in results:
            status = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
            table.add_row(r.name, status, r.message)

        console.print()
        console.print(table)

        # Show details for failed checks
        failed = [r for r in results if not r.passed and r.details]
        if failed:
            console.print("\n[yellow]Details:[/yellow]")
            for r in failed:
                console.print(f"  {r.name}: {r.details}")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
def models():
    """Show available Gemini models."""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            console.print("[red]GEMINI_API_KEY not set[/red]")
            sys.exit(1)

        client = GeminiClient(api_key)
        model_list = client.list_models()

        table = Table(title="Available Gemini Models")
        table.add_column("Model")
        table.add_column("Input Tokens", justify="right")
        table.add_column("Output Tokens", justify="right")

        for m in model_list:
            table.add_row(
                m["name"].replace("models/", ""),
                f"{m['input_token_limit']:,}",
                f"{m['output_token_limit']:,}"
            )

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
