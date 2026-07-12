import sys
import json
import click
import pandas as pd  # type: ignore
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

import unilog
from unilog.detector import detect as detect_format

console = Console()

@click.group()
@click.version_option(version=unilog.__version__)
def cli():
    """unilog — Universal Log Parser CLI."""
    pass

@cli.command(name="parse")
@click.argument("path", required=False)
@click.option("--format", "-f", help="Explicit format to parse (skip auto-detection)")
@click.option("--stdin", is_flag=True, help="Read log lines from standard input")
@click.option("--output", "-o", type=click.Choice(["table", "csv", "json"]), default="table", help="Output format")
@click.option("--head", "-n", type=int, help="Show only the first N lines")
@click.option("--tail", "-t", type=int, help="Show only the last N lines")
@click.option("--chunksize", "-c", type=int, help="Process and output in chunks of N lines")
@click.option("--show-raw", is_flag=True, default=False, help="Show full raw log lines without truncation")
@click.option("--raw-width", type=int, default=80, help="Max width for raw column in table output (default: 80)")
def parse_cmd(
    path: Optional[str],
    format: Optional[str],
    stdin: bool,
    output: str,
    head: Optional[int],
    tail: Optional[int],
    chunksize: Optional[int],
    show_raw: bool,
    raw_width: int
):
    """Parse log file/stream and output records."""
    # Validate input source
    if stdin:
        input_source = sys.stdin
    elif path:
        input_source = path
    else:
        raise click.UsageError("Must provide a log file path or use --stdin flag.")

    effective_raw_width = None if show_raw else raw_width

    # 1. Chunked Parsing option
    if chunksize is not None:
        try:
            chunks = unilog.parse(input_source, format=format, chunksize=chunksize)
            # chunks is a generator of DataFrames
            first = True
            for chunk_df in chunks:
                if head is not None:
                    chunk_df = chunk_df.head(head)
                if tail is not None:
                    chunk_df = chunk_df.tail(tail)
                    
                _output_dataframe(chunk_df, output, is_chunk=True, is_first=first, raw_width=effective_raw_width)
                first = False
            return
        except Exception as e:
            console.print(f"[bold red]Error parsing in chunks: {e}[/bold red]")
            sys.exit(1)

    # 2. Standard single-DataFrame parsing
    try:
        df = unilog.parse(input_source, format=format)
        if not isinstance(df, pd.DataFrame):
            df = pd.concat(list(df), ignore_index=True)
            
        if df.empty:
            console.print("[yellow]No log records parsed.[/yellow]")
            return

        if head is not None:
            df = df.head(head)
        elif tail is not None:
            df = df.tail(tail)

        _output_dataframe(df, output, is_chunk=False, raw_width=effective_raw_width)
    except Exception as e:
        console.print(f"[bold red]Error parsing log: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="detect")
@click.argument("path")
@click.option("--threshold", type=float, default=0.6, help="Confidence threshold")
def detect_cmd(path: str, threshold: float):
    """Detect the format of a log file."""
    try:
        res = detect_format(path, threshold=threshold)
        format_name = res["format"]
        confidence = res["confidence"]
        reason = res["reason"]

        if format_name == "unknown":
            console.print("[bold yellow]Could not confidently detect log format.[/bold yellow]")
            console.print(f"Reason: {reason}")
        else:
            console.print(f"Detected format: [bold green]{format_name}[/bold green] (confidence: {confidence * 100:.1f}%)")
            
            # Show ambiguity warning if applicable
            if res.get("ambiguous") and res.get("alternatives"):
                for alt in res["alternatives"]:
                    console.print(
                        f"[yellow][!] Ambiguous:[/yellow] {alt['format']} is also a close match "
                        f"({alt['confidence'] * 100:.1f}%)"
                    )

        # Print rankings table (zero-score parsers already filtered by detector)
        if res.get("rankings"):
            table = Table(title="Parser Rankings", box=box.ROUNDED)
            table.add_column("Format", style="cyan")
            table.add_column("Confidence Score", style="magenta")
            
            for rank in res["rankings"]:
                score_pct = f"{rank['confidence'] * 100:.1f}%"
                table.add_row(rank["format"], score_pct)
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error detecting format: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="stats")
@click.argument("path")
def stats_cmd(path: str):
    """Compute and display log statistics summary."""
    try:
        s = unilog.stats(path)
        
        console.print(f"[bold cyan]Log Statistics Summary for: {path}[/bold cyan]")
        console.print(f"Format: [bold magenta]{s.get('format', 'unknown')}[/bold magenta]")
        console.print(f"Total lines: {s.get('total_lines', 0)}")
        console.print(f"Error rate: {s.get('error_rate', 0.0) * 100:.2f}%")
        if "http_5xx_rate" in s:
            console.print(f"HTTP 5xx rate: {s.get('http_5xx_rate', 0.0) * 100:.2f}%")
            
        tr = s.get("time_range")
        if tr:
            console.print(f"Time range: {tr[0]} to {tr[1]}")
            
        if s.get("bytes_transferred"):
            console.print(f"Bytes transferred: {s.get('bytes_transferred')} bytes")

        # Top IPs
        top_ips = s.get("top_ips", [])
        if top_ips:
            table = Table(title="Top Client IPs", box=box.SIMPLE_HEAVY)
            table.add_column("IP Address", style="blue")
            table.add_column("Requests", justify="right", style="green")
            for ip, cnt in top_ips:
                table.add_row(ip, str(cnt))
            console.print(table)

        # Log levels
        levels = s.get("log_levels", {})
        if levels:
            table = Table(title="Log Levels Distribution", box=box.SIMPLE_HEAVY)
            table.add_column("Level", style="yellow")
            table.add_column("Count", justify="right", style="green")
            for lvl, cnt in levels.items():
                table.add_row(lvl, str(cnt))
            console.print(table)

        # Top Endpoints
        endpoints = s.get("top_endpoints", [])
        if endpoints:
            table = Table(title="Top Request Endpoints", box=box.SIMPLE_HEAVY)
            table.add_column("Endpoint Path", style="magenta")
            table.add_column("Requests", justify="right", style="green")
            for path_str, cnt in endpoints:
                table.add_row(path_str, str(cnt))
            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error generating stats: {e}[/bold red]")
        sys.exit(1)


@cli.command(name="formats")
def formats_cmd():
    """List all registered log formats."""
    fmts = unilog.list_formats()
    if not fmts:
        console.print("[yellow]No formats registered.[/yellow]")
        return
        
    table = Table(title="Registered Log Formats", box=box.ROUNDED)
    table.add_column("Format Name", style="bold green")
    table.add_column("Description", style="cyan")
    table.add_column("Priority", style="magenta", justify="right")
    table.add_column("Supported Extensions", style="blue")
    
    for f in fmts:
        exts = ", ".join(f.get("supported_extensions", [])) or "None"
        table.add_row(f["name"], f["description"], str(f["priority"]), exts)
        
    console.print(table)


# ==============================================================================
# CLI OUTPUT HELPERS
# ==============================================================================

def _output_dataframe(
    df: pd.DataFrame,
    mode: str,
    is_chunk: bool = False,
    is_first: bool = True,
    raw_width: Optional[int] = 80,
):
    """Format and print DataFrame to stdout based on the mode.
    
    Args:
        raw_width: Max character width for the 'raw' column in table mode.
                   None means no truncation (--show-raw).
    """
    if mode == "csv":
        # Print CSV format (no truncation)
        csv_str = df.to_csv(index=False, header=is_first)
        sys.stdout.write(csv_str)
        sys.stdout.flush()
        
    elif mode == "json":
        # Print JSON format (no truncation)
        if is_chunk:
            for rec in df.to_dict(orient="records"):
                sys.stdout.write(json.dumps(rec, default=str) + "\n")
        else:
            sys.stdout.write(json.dumps(df.to_dict(orient="records"), default=str, indent=2) + "\n")
        sys.stdout.flush()
        
    else:  # table mode
        if is_chunk:
            console.print(f"--- Chunk containing {len(df)} rows ---")
            
        # Rich Table printing
        table = Table(box=box.ROUNDED)
        # Add columns
        for col in df.columns:
            table.add_column(str(col))
            
        # Add up to 50 rows for safety in console
        max_rows = 50
        rows_to_show = df.head(max_rows)
        for _, row in rows_to_show.iterrows():
            cells = []
            for col, val in zip(df.columns, row):
                cell_str = str(val) if val is not None else ""
                # Truncate the raw column in table mode
                if col == "raw" and raw_width is not None and len(cell_str) > raw_width:
                    cell_str = cell_str[:raw_width] + "…"
                cells.append(cell_str)
            table.add_row(*cells)
            
        console.print(table)
        
        if len(df) > max_rows:
            console.print(f"[yellow]... and {len(df) - max_rows} more rows (total: {len(df)})[/yellow]")
