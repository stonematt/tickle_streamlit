"""
Command-line interface for tickle_streamlit.

Provides subcommands for checking, listing, and managing monitored sites.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import load_and_validate_config
from utils.log_util import app_logger
from .core import check_sites

logger = app_logger(__name__)


def cmd_list(args):
    """List all configured sites."""
    try:
        sites = load_and_validate_config(args.config)
        
        if not sites:
            print("No sites configured.")
            return 0
            
        print(f"Configured sites ({len(sites)}):")
        print("-" * 60)
        
        for site in sites:
            status_flags = []
            if site.get("is_streamlit"):
                status_flags.append("Streamlit")
            if site.get("log_raw"):
                status_flags.append("debug")
                
            flags = f" [{', '.join(status_flags)}]" if status_flags else ""
            print(f"• {site['name']:<20} {site['url']:<40}{flags}")
            print(f"  Must contain: '{site['must_contain']}'")
            
        return 0
        
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return 1


def cmd_check(args):
    """Check site uptime."""
    try:
        results = asyncio.run(check_sites(
            config_path=args.config,
            site_name=args.site,
            dry_run=args.dry_run
        ))
        
        # Print summary
        print("\nCheck Results:")
        print("-" * 40)
        for result in results:
            status_symbol = {
                "up": "✅",
                "down": "❌", 
                "restarted": "🔄",
                "error": "⚠️",
                "invalid": "❓",
                "dry_run": "🔍"
            }.get(result["status"], "❓")
            
            print(f"{status_symbol} {result['name']:<20} {result['status']}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Check failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="tickle_streamlit - Streamlit uptime monitoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                           # List all configured sites
  %(prog)s check                          # Check all sites
  %(prog)s check --site lookout           # Check specific site
  %(prog)s check --dry-run                # Check without restarting
        """
    )
    
    parser.add_argument(
        "--config", 
        default="config/sites.json",
        help="Path to sites configuration file (default: config/sites.json)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List configured sites")
    list_parser.set_defaults(func=cmd_list)
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check site uptime")
    check_parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only check content, do not restart"
    )
    check_parser.add_argument(
        "--site", 
        help="Only check the specified site by name"
    )
    check_parser.set_defaults(func=cmd_check)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())