#!/usr/bin/env python3
"""
Main entry point for tickle_streamlit CLI.

Usage: python -m tickle_streamlit <command> [options]
"""

import argparse
import asyncio
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())