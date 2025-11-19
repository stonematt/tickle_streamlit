#!/usr/bin/env python3
"""
Debug script to investigate Streamlit site structure and identify the best way
to detect if a site is running properly.
"""

import asyncio
import json
from playwright.async_api import async_playwright
from utils.config_loader import load_and_validate_config

async def debug_site_structure(site):
    """Debug the structure of a single site."""
    print(f"\n=== DEBUGGING {site['name'].upper()} ===")
    print(f"URL: {site['url']}")
    print(f"Looking for: {site['must_contain']}")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)  # Run headless for server environment
        page = await browser.new_page()
        
        try:
            print(f"\n1. Loading page...")
            await page.goto(site['url'], timeout=15000)
            
            print(f"\n1b. Waiting for content to load...")
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(3000)  # Extra wait for dynamic content
            
            print(f"\n2. Page title: {await page.title()}")
            
            print(f"\n3. Looking for iframes...")
            iframes = await page.query_selector_all('iframe')
            print(f"Found {len(iframes)} iframe(s)")
            
            for i, iframe in enumerate(iframes):
                title = await iframe.get_attribute('title')
                src = await iframe.get_attribute('src')
                print(f"  Iframe {i}: title='{title}', src='{src[:100]}...' if src else 'no src'")
            
            print(f"\n4. Looking for Streamlit-specific elements...")
            # Check for various Streamlit selectors
            selectors_to_check = [
                'iframe[title="streamlitApp"]',
                'iframe[title*="streamlit"]',
                'iframe[src*="streamlit"]',
                'div.stApp',
                '[data-testid="stApp"]',
                '#root',
                'main',
                '.streamlit-container'
            ]
            
            for selector in selectors_to_check:
                element = await page.query_selector(selector)
                if element:
                    print(f"  ✓ Found: {selector}")
                else:
                    print(f"  ✗ Missing: {selector}")
            
            print(f"\n5. Checking page content for expected text...")
            content = await page.content()
            if site['must_contain'] in content:
                print(f"  ✓ Found expected text: '{site['must_contain']}'")
            else:
                print(f"  ✗ Expected text NOT found: '{site['must_contain']}'")
            
            print(f"\n6. Looking for wake-up buttons...")
            wakeup_selectors = [
                'button[data-testid="wakeup-button-owner"]',
                'button[data-testid="wakeup-button-viewer"]',
                'button:has-text("Yes, get this app back up!")',
                'button:has-text("Wake up")',
                'button:has-text("Restart")'
            ]
            
            for selector in wakeup_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    print(f"  ✓ Found wake-up button: {selector} -> '{text}'")
                else:
                    print(f"  ✗ No wake-up button: {selector}")
            
            print(f"\n7. Saving full HTML for inspection...")
            with open(f"logs/debug_{site['name']}_full.html", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Saved to: logs/debug_{site['name']}_full.html")
            
            # Try to get iframe content if iframe exists
            if iframes:
                print(f"\n8. Attempting to access iframe content...")
                for i, iframe in enumerate(iframes):
                    try:
                        frame = await iframe.content_frame()
                        if frame:
                            iframe_content = await frame.content()
                            print(f"  Iframe {i}: Got content ({len(iframe_content)} chars)")
                            
                            if site['must_contain'] in iframe_content:
                                print(f"  ✓ Found expected text in iframe {i}: '{site['must_contain']}'")
                            else:
                                print(f"  ✗ Expected text NOT found in iframe {i}: '{site['must_contain']}'")
                            
                            with open(f"logs/debug_{site['name']}_iframe_{i}.html", "w", encoding="utf-8") as f:
                                f.write(iframe_content)
                            print(f"  Saved iframe {i} to: logs/debug_{site['name']}_iframe_{i}.html")
                        else:
                            print(f"  Iframe {i}: Could not access content frame")
                    except Exception as e:
                        print(f"  Iframe {i}: Error accessing content: {e}")
            
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

async def main():
    """Debug all configured sites."""
    sites = load_and_validate_config("config/sites.json")
    
    print("Streamlit Structure Debug Tool")
    print("=" * 50)
    
    for site in sites:
        await debug_site_structure(site)
    
    print(f"\n=== SUMMARY ===")
    print("Check the logs/debug_*.html files to analyze the actual page structure.")
    print("This will help identify the best selectors for detecting running sites.")

if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())