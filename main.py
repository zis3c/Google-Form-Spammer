import asyncio
import click
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from core import FormParser, SubmissionEngine, is_google_form_url

console = Console()

def render_questions_table(details) -> None:
    from rich.table import Table
    from rich import box

    table = Table(
        title="Detected Questions",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        expand=True,
        padding=(0, 2),
        show_lines=True
    )
    table.add_column("#", style="bold blue", justify="right", no_wrap=True, ratio=1)
    table.add_column("Type", style="bold cyan", no_wrap=True, ratio=3)
    table.add_column("Question Text", style="bold white", ratio=10)
    table.add_column("Options", style="yellow", ratio=8)

    for i, (q_id, q) in enumerate(details.questions.items(), 1):
        opts = ", ".join(q.get("options", [])[:3])
        if len(q.get("options", [])) > 3:
            opts += f" (+{len(q.get('options', []))-3} more)"
        table.add_row(str(i), q["type"], q["text"], opts)

    console.print(table)
    console.print()

def render_summary(engine, count, report_path=None) -> None:
    """Print the run summary, including unverified submissions."""
    stats = engine.stats
    summary = [
        "[bold green]Done![/bold green]",
        f"Requested: {count}",
        f"Successful: [bold green]{stats['success']}[/bold green]",
    ]
    if stats["unverified"]:
        summary.append(f"Unverified: [bold yellow]{stats['unverified']}[/bold yellow]")
    summary.append(f"Failed: [bold red]{stats['failed']}[/bold red]")
    summary.append(f"Retries: [bold yellow]{stats['retries']}[/bold yellow]")
    console.print(Panel("\n".join(summary), title="Summary"))

    if report_path:
        console.print(f"[dim]Report: {report_path}[/dim]")

    if stats['errors']:
        console.print(Panel(str(json.dumps(stats['errors'], indent=2)), title="Error Summary", style="red"))

async def run_submissions(url, count, workers, custom_answer=None, report_path=None):
    parser = FormParser(url)

    try:
        with console.status("[bold cyan]Fetching form details...[/bold cyan]"):
            details = await parser.fetch_details()
    except (ValueError, RuntimeError) as e:
        console.print(f"[bold red]Failed to fetch form:[/bold red] {e}")
        return

    render_questions_table(details)

    engine = SubmissionEngine(details)

    console.print(f"[bold yellow]Starting {count} submissions with {workers} workers...[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        transient=False,
        expand=True
    ) as progress:
        task = progress.add_task("[green]Submitting...", total=count)

        def update_progress(success):
            progress.update(task, advance=1)

        await engine.run(count, workers, custom_text=custom_answer,
                         progress_callback=update_progress, report_path=report_path)

    render_summary(engine, count, report_path)

class RichHelpCommand(click.Command):
    def format_help(self, ctx, formatter):
        console.print()
        console.print("[bold magenta]Google Forms Spammer - Educational Tool[/bold magenta]\n")
        console.print("[bold cyan]Usage:[/bold cyan] [white]python main.py [OPTIONS][/white]\n")
        
        from rich.table import Table
        from rich import box
        
        table = Table(box=None, padding=(0, 2), expand=False, show_header=False)
        table.add_column("Option", style="bold green")
        table.add_column("Description", style="white")
        table.add_column("Default", style="dim")

        for param in self.get_params(ctx):
            name = "--" + param.name.replace("_", "-")
            if param.secondary_opts:
                 name += ", " + ", ".join(param.secondary_opts)
            
            help_text = param.help or ""
            default = f"(default: {param.default})" if param.default is not None and str(param.default) != "None" else ""
            
            table.add_row(name, help_text, default)
            
        console.print("[bold yellow]Options:[/bold yellow]")
        console.print(table)

@click.command(cls=RichHelpCommand)
@click.option('--url', help='Google Form URL')
@click.option('--count', default=100, help='Number of requests to send', type=int)
@click.option('--workers', default=50, help='Number of concurrent workers', type=int)
@click.option('--custom-answer', help='Custom answer for text fields')
@click.option('--report', 'report', type=click.Path(dir_okay=False), help='Write a JSONL log of every submission to this path')
def main(url, count, workers, custom_answer, report):
    """Google Forms Spammer - Educational Tool"""
    
    if not url:
        console.print(r"""[bold red]
╺━┓╻┏━┓┏━┓┏━╸   ┏━╸┏━╸┏━┓┏━┓┏┳┓   ┏━┓┏━┓┏━┓┏┳┓┏┳┓┏━╸┏━┓
┏━┛┃┗━┓╺━┫┃     ┃╺┓┣╸ ┃ ┃┣┳┛┃┃┃   ┗━┓┣━┛┣━┫┃┃┃┃┃┃┣╸ ┣┳┛
┗━╸╹┗━┛┗━┛┗━╸   ┗━┛╹  ┗━┛╹┗╸╹ ╹   ┗━┛╹  ╹ ╹╹ ╹╹ ╹┗━╸╹┗╸
[/bold red]""")
        try:
            while True:
                url = Prompt.ask("Enter Google Form URL")
                if is_google_form_url(url):
                    break
                console.print("[bold red]Invalid URL![/bold red] Please use a valid Google Forms link.\nExample: [dim]https://docs.google.com/forms/d/e/xxxxx/viewform[/dim]\n")
        except KeyboardInterrupt:
            console.print("\n[bold red]Aborted![/bold red]")
            return
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def interactive_flow():
            parser = FormParser(url)
            try:
                with console.status("[bold cyan]Fetching form details...[/bold cyan]"):
                    details = await parser.fetch_details()
            except (ValueError, RuntimeError) as e:
                console.print(f"[bold red]Failed to fetch form:[/bold red] {e}")
                return

            render_questions_table(details)

            nonlocal count, workers, custom_answer
            
            while True:
                custom_config = {}

                mode_panel = Panel(
                    "[bold green]1. Random Mode[/bold green]\n"
                    "   [dim]Automatically fills form with realistic random data.[/dim]\n\n"
                    "[bold yellow]2. Custom Mode (Web UI)[/bold yellow]\n"
                    "   [dim]Launch a visual editor to define specific answers.[/dim]",
                    title="[bold magenta]Select Attack Mode[/bold magenta]",
                    border_style="magenta"
                )
                console.print(mode_panel)
                
                mode_input = Prompt.ask(
                    "[bold cyan]Choose Option[/bold cyan]", 
                    choices=["1", "2"], 
                    default="1",
                    show_choices=False
                )

                if mode_input == "2":
                    from configurator import run_configurator
                    
                    console.print(Panel(
                        "[bold]Server running at:[/bold] [link=http://localhost:8080]http://localhost:8080[/link]\n"
                        "[dim](Click the link above or open in browser)[/dim]",
                        title="[bold yellow]Web Configurator Launched[/bold yellow]",
                        border_style="yellow"
                    ))
                    
                    with console.status("[bold cyan]Waiting for configuration...[/bold cyan]", spinner="dots"):
                        custom_config = await run_configurator(details)
                    
                    console.print(f"[bold green]✓ Configuration loaded for {len(custom_config)} fields[/bold green]")
                else:
                     console.print("[dim]Using Random Generation[/dim]")
                
                console.print()
                console.rule("[bold red]Attack Parameters[/bold red]")
                count = IntPrompt.ask("[:rocket:] [bold cyan]Number of Requests[/bold cyan]", default=count)
                workers = IntPrompt.ask("[:zap:] [bold cyan]Concurrent Workers[/bold cyan]", default=workers)
                console.print()
                
                engine = SubmissionEngine(details)
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=None),
                    TaskProgressColumn(),
                    transient=False,
                    expand=True
                ) as progress:
                    task = progress.add_task("[green]Submitting...", total=count)
                    
                    def update_progress(success):
                        progress.update(task, advance=1)

                    await engine.run(
                        count, 
                        workers, 
                        custom_text=custom_answer, 
                        custom_config=custom_config,
                        progress_callback=update_progress,
                        report_path=report
                    )
                    
                render_summary(engine, count, report)
                
                console.print()
                if not Confirm.ask("[bold cyan]Run another batch?[/bold cyan]"):
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                console.print()

        try:
            loop.run_until_complete(interactive_flow())
        except KeyboardInterrupt:
            console.print("\n[bold red]Aborted![/bold red]")
            return
        
    else:
        asyncio.run(run_submissions(url, count, workers, custom_answer, report))

if __name__ == '__main__':
    try:
        main(standalone_mode=False)
    except click.exceptions.Abort:
         console.print("\n[bold red]Aborted![/bold red]")
    except click.exceptions.UsageError as e:
         console.print(f"\n[bold red]Error:[/bold red] {e.message}")
         if e.ctx:
             console.print(f"[dim]{e.ctx.get_help()}[/dim]")
         else:
             console.print("[dim]Run 'python main.py --help' for usage information.[/dim]")
    except Exception as e:
         console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
