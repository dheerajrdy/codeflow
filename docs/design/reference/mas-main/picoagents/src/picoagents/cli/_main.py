"""
Main CLI entry point for PicoAgents.

Provides a unified command-line interface with subcommands for different functionality.
"""

import argparse
import sys
from typing import List, Optional


def main(args: Optional[List[str]] = None) -> None:
    """Main CLI entry point with subcommands.

    Args:
        args: Optional list of arguments (for testing)
    """
    parser = argparse.ArgumentParser(
        prog="picoagents",
        description="PicoAgents - Lightweight AI agent framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  ui          Launch web interface for agents/orchestrators/workflows

Examples:
  picoagents ui                    # Launch UI for current directory
  picoagents ui --dir ./agents     # Launch UI for specific directory
  picoagents ui --port 8000        # Use different port
        """,
    )

    # Add version flag
    parser.add_argument("--version", action="version", version="picoagents 0.1.0")

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="<command>",
    )

    # UI subcommand
    ui_parser = subparsers.add_parser(
        "ui",
        help="Launch web interface",
        description="Launch PicoAgents web interface for interacting with entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  picoagents ui                    # Scan current directory
  picoagents ui --dir ./agents     # Scan specific directory
  picoagents ui --port 8000        # Use different port
  picoagents ui --no-open          # Don't open browser
  picoagents ui --reload           # Enable auto-reload for development
        """,
    )

    ui_parser.add_argument(
        "--dir",
        default=".",
        help="Directory to scan for agents, orchestrators, and workflows (default: current directory)",
    )
    ui_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="Port to run server on (default: 8080)",
    )
    ui_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind server to (default: 127.0.0.1)",
    )
    ui_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't automatically open browser",
    )
    ui_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    ui_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)",
    )

    # Parse arguments
    parsed_args = parser.parse_args(args)

    # Handle no command provided
    if parsed_args.command is None:
        parser.print_help()
        print("\n💡 Tip: Try 'picoagents ui' to launch the web interface")
        sys.exit(1)

    # Route to appropriate handler
    if parsed_args.command == "ui":
        _handle_ui_command(parsed_args)
    else:
        parser.print_help()
        sys.exit(1)


def _handle_ui_command(args: argparse.Namespace) -> None:
    """Handle the 'ui' subcommand.

    Args:
        args: Parsed arguments for the ui command
    """
    try:
        from ..webui import webui

        webui(
            entities_dir=args.dir,
            port=args.port,
            host=args.host,
            auto_open=not args.no_open,
            reload=args.reload,
            log_level=args.log_level,
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down PicoAgents UI")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Error importing WebUI: {e}")
        print("💡 Make sure to install web dependencies: pip install picoagents[web]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
