import asyncio
import click
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from core import FormParser, AsyncFormSpammer

console = Console()

async def run_spam(url, count, workers, custom_answer=None):
    """Orchestrates the spamming process."""
    parser = FormParser(url)
    
    with console.status("[bold cyan]Fetching form details...[/bold cyan]"):
        details = await parser.fetch_details()
    
    if not details:
        console.print("[bold red]Failed to fetch or parse the form.[/bold red]")
        return

    console.print(f"[green]Successfully parsed {len(details.questions)} questions.[/green]")
    console.print(Panel(str(json.dumps(details.questions, indent=2)), title="Detected Questions", expand=False))

    spammer = AsyncFormSpammer(details)
    
    console.print(f"[bold yellow]Starting async spam attack with {count} requests using {workers} workers...[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        transient=False,
    ) as progress:
        task = progress.add_task("[green]Spamming...", total=count)
        
        def update_progress(success):
            progress.update(task, advance=1)
            
        await spammer.run(count, workers, custom_text=custom_answer, progress_callback=update_progress)

    console.print(Panel(f"[bold green]Attack Complete![/bold green]\n\n"
                        f"Requested: {count}\n"
                        f"Successful: [bold green]{spammer.stats['success']}[/bold green]\n"
                        f"Failed: [bold red]{spammer.stats['failed']}[/bold red]\n"
                        f"Retries: [bold yellow]{spammer.stats['retries']}[/bold yellow]",
                        title="Summary"))

    if spammer.stats['errors']:
        console.print(Panel(str(json.dumps(spammer.stats['errors'], indent=2)), title="Error Summary", style="red"))

@click.command()
@click.option('--url', help='Google Form URL')
@click.option('--count', default=100, help='Number of requests to send', type=int)
@click.option('--workers', default=50, help='Number of concurrent workers', type=int)
@click.option('--custom-answer', help='Custom answer for text fields')
def main(url, count, workers, custom_answer):
    """Google Forms Spammer - Educational Tool"""
    
    # Interactive mode if URL is not provided
    if not url:
        console.print(r"""[bold red]
╺━┓╻┏━┓┏━┓┏━╸   ┏━╸┏━╸┏━┓┏━┓┏┳┓   ┏━┓┏━┓┏━┓┏┳┓┏┳┓┏━╸┏━┓
┏━┛┃┗━┓╺━┫┃     ┃╺┓┣╸ ┃ ┃┣┳┛┃┃┃   ┗━┓┣━┛┣━┫┃┃┃┃┃┃┣╸ ┣┳┛
┗━╸╹┗━┛┗━┛┗━╸   ┗━┛╹  ┗━┛╹┗╸╹ ╹   ┗━┛╹  ╹ ╹╹ ╹╹ ╹┗━╸╹┗╸
[/bold red]""")
        url = Prompt.ask("Enter Google Form URL")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # We need to run fetch first to confirm to user? 
        # Actually, let's just mimic the flow.
        # But run_spam does fetching. So we just need to get the URL found.
        
        # If interactive, we usually want to confirm questions *before* spamming.
        # My run_spam does it all. Let's refactor run_spam slightly or just ask user valid questions here.
        # Ideally, we fetch, show, ask confirm, then spam.
        
        # Let's do it properly inside an async main wrapper for interactive
        async def interactive_flow():
            parser = FormParser(url)
            with console.status("[bold cyan]Fetching form details...[/bold cyan]"):
                details = await parser.fetch_details()
            
            if not details:
                console.print("[bold red]Failed to fetch form.[/bold red]")
                return

            console.print(Panel(str(json.dumps(details.questions, indent=2)), title="Detected Questions", expand=False))
            
            if not Confirm.ask("Do these questions look correct?"):
                 return
            
            nonlocal custom_answer, count, workers
            
            if not custom_answer:
                mode = Prompt.ask("Random or Custom answers?", choices=["r", "c"], default="r")
                if mode == "c":
                    custom_answer = Prompt.ask("Custom answer")
            
            count = IntPrompt.ask("How many requests?", default=count)
            workers = IntPrompt.ask("Concurrent workers?", default=workers)
            
            spammer = AsyncFormSpammer(details)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                transient=False,
            ) as progress:
                task = progress.add_task("[green]Spamming...", total=count)
                await spammer.run(count, workers, custom_text=custom_answer, progress_callback=lambda s: progress.update(task, advance=1))
                
            console.print(Panel(f"[bold green]Done![/bold green]\n"
                                f"Success: [bold green]{spammer.stats['success']}[/bold green]\n"
                                f"Failed: [bold red]{spammer.stats['failed']}[/bold red]\n"
                                f"Retries: [bold yellow]{spammer.stats['retries']}[/bold yellow]",
                                title="Summary"))

            if spammer.stats['errors']:
                console.print(Panel(str(json.dumps(spammer.stats['errors'], indent=2)), title="Error Summary", style="red"))

        loop.run_until_complete(interactive_flow())
        
    else:
        # Headless/CLI mode
        asyncio.run(run_spam(url, count, workers, custom_answer))

if __name__ == '__main__':
    main()
