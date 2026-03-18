"""Browser utility for kb-tool - uses system Chrome when available."""

import shutil
from typing import Optional


def find_system_chrome() -> Optional[str]:
    """Find system-installed Chrome/Chromium binary.

    Returns:
        Path to Chrome executable, or None if not found.
    """
    candidates = [
        'google-chrome-stable',
        'google-chrome',
        'chromium-browser',
        'chromium',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
    ]
    for name in candidates:
        path = shutil.which(name) if not name.startswith('/') else (name if __import__('os').path.exists(name) else None)
        if path:
            return path
    return None


def launch_browser(playwright, headless: bool = True):
    """Launch browser using system Chrome if available, else Playwright's.

    Args:
        playwright: Playwright sync_api instance
        headless: Whether to run headless

    Returns:
        Browser instance
    """
    chrome_path = find_system_chrome()

    if chrome_path:
        return playwright.chromium.launch(
            executable_path=chrome_path,
            headless=headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
    else:
        # Fallback to Playwright's bundled browser
        return playwright.chromium.launch(headless=headless)
