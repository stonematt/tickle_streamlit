"""
Command-line interface for tickle_streamlit.

Provides subcommands for checking, listing, and managing monitored sites.
"""

import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from utils.config_loader import load_and_validate_config, is_valid_url
from utils.log_util import app_logger
import core
check_sites = core.check_sites

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
        # Use positional argument or legacy --site flag
        site_name = args.site or args.site_flag
        results = asyncio.run(check_sites(
            config_path=args.config,
            site_name=site_name,
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


def backup_config(config_path: Path) -> Path:
    """Create a backup of the config file."""
    if not config_path.exists():
        return config_path  # No backup needed if file doesn't exist
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"sites.json.backup_{timestamp}"
    shutil.copy2(config_path, backup_path)
    return backup_path


def restore_config(config_path: Path, backup_path: Path) -> bool:
    """Restore config from backup."""
    try:
        if backup_path.exists():
            shutil.copy2(backup_path, config_path)
            return True
    except Exception:
        pass
    return False


def validate_site_data(name: str, url: str, must_contain: str) -> List[str]:
    """Validate site data and return list of errors."""
    errors = []
    
    # Name validation
    if not name or not name.strip():
        errors.append("Site name cannot be empty")
    elif len(name.strip()) < 2:
        errors.append("Site name must be at least 2 characters")
    elif not all(c.isalnum() or c in '-_' for c in name):
        errors.append("Site name can only contain letters, numbers, hyphens, and underscores")
    
    # URL validation
    if not url or not url.strip():
        errors.append("URL cannot be empty")
    elif not is_valid_url(url.strip()):
        errors.append("Invalid URL format")
    
    # Must contain validation
    if not must_contain or not must_contain.strip():
        errors.append("Must contain text cannot be empty")
    elif len(must_contain.strip()) < 3:
        errors.append("Must contain text must be at least 3 characters")
    
    return errors


def interactive_add_site(config_path: Path) -> bool:
    """Interactive mode for adding a site."""
    print("🔧 Interactive Site Addition")
    print("=" * 40)
    
    # Get site name
    while True:
        name = input("Site name (unique identifier): ").strip()
        errors = validate_site_data(name, "https://example.com", "test")
        name_errors = [e for e in errors if "name" in e.lower()]
        if not name_errors:
            break
        print(f"❌ {', '.join(name_errors)}")
    
    # Get URL
    while True:
        url = input("Site URL (e.g., https://example.com): ").strip()
        errors = validate_site_data("test", url, "test")
        url_errors = [e for e in errors if "url" in e.lower()]
        if not url_errors:
            break
        print(f"❌ {', '.join(url_errors)}")
    
    # Get must_contain
    while True:
        must_contain = input("Text that must be present on page: ").strip()
        errors = validate_site_data("test", "https://example.com", must_contain)
        content_errors = [e for e in errors if "must contain" in e.lower()]
        if not content_errors:
            break
        print(f"❌ {', '.join(content_errors)}")
    
    # Get optional settings
    streamlit = input("Is this a Streamlit app? (y/N): ").strip().lower() in ('y', 'yes')
    debug = input("Enable debug logging? (y/N): ").strip().lower() in ('y', 'yes')
    
    selector = input(f"CSS selector (default: {'div.stApp' if streamlit else 'body'}): ").strip()
    if not selector:
        selector = "div.stApp" if streamlit else "body"
    
    # Show summary
    print("\n📋 Site Summary:")
    print(f"  Name: {name}")
    print(f"  URL: {url}")
    print(f"  Must contain: '{must_contain}'")
    print(f"  Selector: {selector}")
    print(f"  Streamlit: {streamlit}")
    print(f"  Debug logging: {debug}")
    
    confirm = input("\nAdd this site? (y/N): ").strip().lower()
    if confirm not in ('y', 'yes'):
        print("❌ Cancelled")
        return False
    
    # Add the site
    try:
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                sites = json.load(f)
        else:
            sites = []
        
        # Check for duplicate names
        existing_names = [site.get('name') for site in sites]
        if name in existing_names:
            print(f"❌ Site '{name}' already exists")
            return False
        
        # Create new site entry
        new_site = {
            "name": name,
            "url": url,
            "selector": selector,
            "must_contain": must_contain,
            "is_streamlit": streamlit,
            "log_raw": debug
        }
        
        sites.append(new_site)
        
        # Save config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(sites, f, indent=2)
        
        print(f"✅ Added site '{name}' to configuration")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add site: {e}")
        return False


def cmd_add(args):
    """Add a new site to configuration."""
    try:
        config_path = Path(args.config)
        
        # Interactive mode
        if args.interactive:
            return 0 if interactive_add_site(config_path) else 1
        
        # Validate input data
        errors = validate_site_data(args.name, args.url, args.must_contain)
        if errors:
            print(f"❌ Validation errors: {', '.join(errors)}")
            return 1
        
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                sites = json.load(f)
        else:
            sites = []
        
        # Check for duplicate names
        existing_names = [site.get('name') for site in sites]
        if args.name in existing_names:
            print(f"❌ Site '{args.name}' already exists")
            return 1
        
        # Create new site entry
        selector = args.selector or ("div.stApp" if args.streamlit else "body")
        new_site = {
            "name": args.name,
            "url": args.url,
            "selector": selector,
            "must_contain": args.must_contain,
            "is_streamlit": args.streamlit,
            "log_raw": args.debug
        }
        
        # Dry run mode
        if args.dry_run:
            print("🔍 Dry run - would add the following site:")
            print(json.dumps(new_site, indent=2))
            return 0
        
        # Create backup
        backup_path = backup_config(config_path)
        
        try:
            sites.append(new_site)
            
            # Save config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(sites, f, indent=2)
            
            print(f"✅ Added site '{args.name}' to configuration")
            print(f"   URL: {args.url}")
            print(f"   Must contain: '{args.must_contain}'")
            print(f"   Selector: {selector}")
            if args.streamlit:
                print("   Streamlit app: yes")
            if args.debug:
                print("   Debug logging: yes")
            
            return 0
            
        except Exception as e:
            # Restore from backup on failure
            if restore_config(config_path, backup_path):
                print("🔄 Restored config from backup due to error")
            raise e
        
    except Exception as e:
        logger.error(f"Failed to add site: {e}")
        print(f"❌ Failed to add site: {e}")
        return 1


def cmd_remove(args):
    """Remove a site from configuration."""
    try:
        config_path = Path(args.config)
        
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            return 1
        
        with open(config_path, 'r') as f:
            sites = json.load(f)
        
        # Find and remove site
        original_count = len(sites)
        sites = [site for site in sites if site.get('name') != args.name]
        
        if len(sites) == original_count:
            print(f"❌ Site '{args.name}' not found")
            return 1
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(sites, f, indent=2)
        
        print(f"✅ Removed site '{args.name}' from configuration")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to remove site: {e}")
        return 1


def cmd_validate(args):
    """Validate configuration file."""
    try:
        sites = load_and_validate_config(args.config)
        
        if not sites:
            print("⚠️  No sites configured")
            return 0
        
        print(f"✅ Configuration is valid ({len(sites)} sites)")
        
        # Show validation details
        for site in sites:
            name = site.get('name', 'unnamed')
            url = site.get('url', 'missing')
            required = site.get('must_contain', 'missing')
            
            issues = []
            if not url.startswith(('http://', 'https://')):
                issues.append("invalid URL")
            if not required:
                issues.append("missing must_contain")
            
            if issues:
                print(f"  ⚠️  {name}: {', '.join(issues)}")
            else:
                print(f"  ✅ {name}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
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
  %(prog)s check lookout                  # Check specific site
  %(prog)s check --site lookout           # Check specific site (legacy)
  %(prog)s check --dry-run                # Check without restarting
  %(prog)s add mysite https://example.com "Welcome" --streamlit
  %(prog)s add --interactive              # Interactive guided addition
  %(prog)s add mysite https://example.com "Welcome" --dry-run  # Preview before adding
  %(prog)s remove mysite                  # Remove site from config
  %(prog)s validate                       # Validate configuration
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
        "site", 
        nargs='?',
        help="Site name to check (optional, checks all if not provided)"
    )
    check_parser.add_argument(
        "--site", 
        dest="site_flag",
        help="Only check the specified site by name (legacy)"
    )
    check_parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Only check content, do not restart"
    )
    check_parser.set_defaults(func=cmd_check)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new site to configuration")
    add_parser.add_argument("name", nargs='?', help="Site name (unique identifier)")
    add_parser.add_argument("url", nargs='?', help="Site URL")
    add_parser.add_argument("must_contain", nargs='?', help="Text that must be present on page")
    add_parser.add_argument("--streamlit", action="store_true", help="Site is a Streamlit app")
    add_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    add_parser.add_argument("--selector", help="CSS selector (default: div.stApp for Streamlit, body for others)")
    add_parser.add_argument("--dry-run", action="store_true", help="Show what would be added without modifying config")
    add_parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode for guided site addition")
    add_parser.set_defaults(func=cmd_add)
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a site from configuration")
    remove_parser.add_argument("name", help="Site name to remove")
    remove_parser.set_defaults(func=cmd_remove)
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration file")
    validate_parser.set_defaults(func=cmd_validate)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())