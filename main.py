import asyncio
import click
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from core import FormParser, SubmissionEngine, is_google_form_url

console = Console()

async def run_submissions(url, count, workers, custom_answer=None, custom_config=None, report_path=None):
    """Orchestrates the submission run."""
    parser = FormParser(url)
    try:
        with console.status("[bold cyan]Mengambil detail form...[/bold cyan]"):
            details = await parser.fetch_details()
    except (ValueError, RuntimeError) as e:
        console.print(f"[bold red]Gagal mengambil form:[/bold red] {e}")
        return

    render_questions_table(details)

    await run_engine(details, count, workers, custom_answer, custom_config, report_path)

def render_questions_table(details) -> None:

    """Render the detected-questions table (shared by run_submissions and interactive_flow)."""
    from rich.table import Table
    from rich import box

    table = Table(
        title="Pertanyaan Terdeteksi",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        expand=True,
        padding=(0, 2),
        show_lines=True,
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


def _quota_check(engine, custom_config) -> None:
    """Compare per-option quota targets with what was actually accepted."""
    from rich.table import Table
    from rich import box

    pools = {k[:-6]: v for k, v in (custom_config or {}).items() if k.endswith("__pool")}
    if not pools:
        return

    mismatches = []
    for q_id, pool in pools.items():
        actual = {k.lower(): v for k, v in engine.distributions.get(q_id, {}).items()}
        for entry in pool:
            quota = entry.get("quota")
            if not quota:
                continue
            sent = actual.get(str(entry["value"]).strip().lower(), 0)
            if sent != quota:
                mismatches.append((q_id, str(entry["value"]), quota, sent))

    if not mismatches:
        console.print(f"[green]Kuota sesuai target untuk {len(pools)} pertanyaan berkuota.[/green]")
        return

    table = Table(title="Kuota tidak sesuai target", box=box.ROUNDED, header_style="bold yellow")
    table.add_column("Pertanyaan", style="bold white")
    table.add_column("Opsi", style="white")
    table.add_column("Target", justify="right", style="cyan")
    table.add_column("Terkirim", justify="right", style="red")
    for row in mismatches[:30]:
        table.add_row(*map(str, row))
    console.print(table)
    if len(mismatches) > 30:
        console.print(f"[dim]+{len(mismatches) - 30} baris lainnya; lihat laporan.[/dim]")


async def run_engine(details, count, workers, custom_answer=None, custom_config=None, report_path=None) -> None:
    """Runs the submission engine with shared progress UI (used by both run_submissions and interactive_flow)."""
    engine = SubmissionEngine(details)

    console.print(f"[bold yellow]Memulai {count} pengiriman dengan {workers} pekerja...[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        transient=False,
        expand=True
    ) as progress:
        task = progress.add_task("[green]Mengirim...", total=count)

        def update_progress(success):
            progress.update(task, advance=1)

        await engine.run(count, workers, custom_text=custom_answer, custom_config=custom_config,
                         progress_callback=update_progress, report_path=report_path)

    stats = engine.stats
    summary = [
        "[bold green]Selesai![/bold green]",
        f"Berhasil: [bold green]{stats['success']}[/bold green]",
    ]
    if stats["unverified"]:
        summary.append(f"Tidak terverifikasi: [bold yellow]{stats['unverified']}[/bold yellow]")
    summary.append(f"Gagal: [bold red]{stats['failed']}[/bold red]")
    summary.append(f"Ulang coba: [bold yellow]{stats['retries']}[/bold yellow]")
    console.print(Panel("\n".join(summary), title="Ringkasan"))

    _quota_check(engine, custom_config)

    if report_path:
        console.print(f"[dim]Laporan: {report_path}[/dim]")

    if engine.stats['errors']:
        console.print(Panel(str(json.dumps(engine.stats['errors'], indent=2)), title="Ringkasan Error", style="red"))

class RichHelpCommand(click.Command):
    def format_help(self, ctx, formatter):
        console.print()
        console.print("[bold magenta]FormForge - Google Forms Runner[/bold magenta]\n")
        console.print("[bold cyan]Usage:[/bold cyan] [white]python main.py [OPTIONS][/white]\n")
        
        from rich.table import Table
        from rich import box
        from click.core import UNSET

        table = Table(box=None, padding=(0, 2), expand=False, show_header=False)
        table.add_column("Option", style="bold green")
        table.add_column("Description", style="white")
        table.add_column("Default", style="dim")

        for param in self.get_params(ctx):
            name = ", ".join(param.opts + param.secondary_opts)
            if not name:
                continue

            help_text = param.help or ""
            default = ""
            if param.default is not None and param.default is not UNSET:
                default = f"(default: {param.default})"

            table.add_row(name, help_text, default)
            
        console.print("[bold yellow]Options:[/bold yellow]")
        console.print(table)

@click.command(cls=RichHelpCommand)
@click.option('--url', help='Google Form URL')
@click.option('--count', default=100, help='Number of requests to send', type=int)
@click.option('--workers', default=50, help='Number of concurrent workers', type=int)
@click.option('--custom-answer', help='Custom answer for text fields')
@click.option('--preset', 'preset', type=click.Path(exists=True, dir_okay=False), help='JSON preset with weighted pools (see configurator)')
@click.option('--report', 'report', type=click.Path(dir_okay=False), help='Write a JSONL log of every submission to this path')
@click.pass_context
def main(ctx, url, count, workers, custom_answer, preset, report):
    """FormForge - Google Forms automation for authorized testing."""
    
    custom_config = None
    if preset:
        with open(preset, encoding="utf-8") as f:
            data = json.load(f)
        custom_config = data.get("config", data)
        # Only fill parameters the user did not pass explicitly
        if ctx.get_parameter_source("count") == click.core.ParameterSource.DEFAULT:
            count = data.get("count", count)
        if ctx.get_parameter_source("workers") == click.core.ParameterSource.DEFAULT:
            workers = data.get("workers", workers)
        url = url or data.get("url")
    
    # Interactive mode if URL is not provided
    if not url:
        console.print(r"""[bold red]
╺━┓╻┏━┓┏━┓┏━╸   ┏━╸┏━╸┏━┓┏━┓┏┳┓   ┏━┓┏━┓┏━┓┏┳┓┏┳┓┏━╸┏━┓
┏━┛┃┗━┓╺━┫┃     ┃╺┓┣╸ ┃ ┃┣┳┛┃┃┃   ┗━┓┣━┛┣━┫┃┃┃┃┃┃┣╸ ┣┳┛
┗━╸╹┗━┛┗━┛┗━╸   ┗━┛╹  ┗━┛╹┗╸╹ ╹   ┗━┛╹  ╹ ╹╹ ╹╹ ╹┗━╸╹┗╸
[/bold red]""")
        try:
            while True:
                url = Prompt.ask("Masukkan URL Google Form")
                if is_google_form_url(url):
                    break
                console.print("[bold red]URL tidak valid![/bold red] Silakan gunakan tautan Google Forms yang benar.\nContoh: [dim]https://docs.google.com/forms/d/e/xxxxx/viewform[/dim]\n")
        except KeyboardInterrupt:
            console.print("\n[bold red]Aborted![/bold red]")
            return
        
        # We need to run fetch first to confirm to user? 
        # Actually, let's just mimic the flow.
        # But run_submissions does fetching. So we just need to get the URL found.
        
        # If interactive, we usually want to confirm questions before submitting.
        # run_submissions does all of it, so confirmation happens inside it.
        # Ideally, we fetch, show, ask confirm, then submit.
        
        # Let's do it properly inside an async main wrapper for interactive
        async def interactive_flow():
            parser = FormParser(url)
            try:
                with console.status("[bold cyan]Mengambil detail form...[/bold cyan]"):
                    details = await parser.fetch_details()
            except (ValueError, RuntimeError) as e:
                console.print(f"[bold red]Gagal mengambil form:[/bold red] {e}")
                return

            render_questions_table(details)

            nonlocal count, workers, custom_answer
            
            while True:
                custom_config = {}

                # Mode Selection Panel
                mode_panel = Panel(
                    "[bold green]1. Random Mode[/bold green]\n"
                    "   [dim]Automatically fills form with realistic random data.[/dim]\n\n"
                    "[bold yellow]2. Custom Mode (Web UI)[/bold yellow]\n"
                    "   [dim]Launch a visual editor to define specific answers.[/dim]",
                    title="[bold magenta]Select Answer Mode[/bold magenta]",
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

                    custom_config, config_url = await run_configurator(details)
                    console.print(Panel(
                        f"[bold]Server running at:[/bold] [link={config_url}]{config_url}[/link]\n"
                        "[dim](Klik tautan di atas atau buka di browser)[/dim]",
                        title="[bold yellow]Web Configurator Diluncurkan[/bold yellow]",
                        border_style="yellow"
                    ))
                else:
                     console.print("[dim]Using Random Generation[/dim]")
                
                console.print()
                console.rule("[bold red]Run Parameters[/bold red]")
                count = IntPrompt.ask("[:rocket:] [bold cyan]Number of Requests[/bold cyan]", default=count)
                workers = IntPrompt.ask("[:zap:] [bold cyan]Concurrent Workers[/bold cyan]", default=workers)
                console.print()
                await run_engine(details, count, workers, custom_answer, custom_config, report)
                
                console.print()
                if not Confirm.ask("[bold cyan]Run another batch?[/bold cyan]"):
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                console.print()

        try:
            asyncio.run(interactive_flow())
        except KeyboardInterrupt:
            console.print("\n[bold red]Aborted![/bold red]")
            return
        
    else:
        # Headless/CLI mode
        asyncio.run(run_submissions(url, count, workers, custom_answer, custom_config, report))

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
        import traceback
        traceback.print_exc()
        sys.exit(1)
