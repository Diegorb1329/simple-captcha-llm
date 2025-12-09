"""
Capture the captcha image from the SAT certificate recovery page.

Usage:
  python capture_captcha.py
  python capture_captcha.py --output /path/to/save/captcha.png
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_URL = (
    "https://portalsat.plataforma.sat.gob.mx/RecuperacionDeCertificados/"
    "faces/recuperaRFC.xhtml"
)

DEFAULT_OUTPUT = Path(__file__).parent.parent / "outputs" / "captcha.png"


def capture_captcha(url: str, output_path: Path, timeout: int = 20) -> Path:
    """Navigate to the SAT page and capture the captcha image."""
    
    # Configure Chrome options
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    # Ignore SSL errors (SAT has certificate issues)
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if we're on the results page and need to go back to input form
        try:
            regresar_btn = driver.find_element(By.XPATH, "//input[@value='Regresar']")
            if regresar_btn:
                print("Found 'Regresar' button, clicking to go to input form...")
                regresar_btn.click()
                time.sleep(3)
        except Exception:
            pass
        
        # Try to find the captcha image - it's usually in an img tag
        # Look for common captcha patterns
        captcha_selectors = [
            "img[src*='captcha']",
            "img[src*='Captcha']",
            "img[src*='CAPTCHA']",
            "img[src*='jcaptcha']",
            "img[src*='kaptcha']",
            "img[id*='captcha']",
            "img[id*='Captcha']",
            "img[class*='captcha']",
            "//img[contains(@src, 'captcha')]",
            "//img[contains(@src, 'Captcha')]",
        ]
        
        captcha_element = None
        
        # Try CSS selectors first
        for selector in captcha_selectors[:8]:
            try:
                captcha_element = driver.find_element(By.CSS_SELECTOR, selector)
                if captcha_element:
                    print(f"Found captcha with selector: {selector}")
                    break
            except Exception:
                continue
        
        # Try XPath selectors
        if not captcha_element:
            for selector in captcha_selectors[8:]:
                try:
                    captcha_element = driver.find_element(By.XPATH, selector)
                    if captcha_element:
                        print(f"Found captcha with XPath: {selector}")
                        break
                except Exception:
                    continue
        
        # If still not found, look for any image that might be a captcha
        if not captcha_element:
            print("Searching for captcha image in all images...")
            images = driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                src = img.get_attribute("src") or ""
                alt = img.get_attribute("alt") or ""
                img_id = img.get_attribute("id") or ""
                
                # Skip known non-captcha images
                if "sat_nuevo" in src or "logo" in src.lower():
                    continue
                    
                # Check dimensions - captchas are usually small
                width = img.size.get("width", 0)
                height = img.size.get("height", 0)
                
                if 50 < width < 400 and 20 < height < 150:
                    print(f"Found potential captcha: src={src[:50]}... size={width}x{height}")
                    captcha_element = img
                    break
        
        if not captcha_element:
            # Take full page screenshot as fallback
            print("Could not find captcha element, taking full page screenshot...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(output_path))
            print(f"Full page screenshot saved to: {output_path}")
            return output_path
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Take screenshot of the captcha element
        captcha_element.screenshot(str(output_path))
        print(f"Captcha saved to: {output_path}")
        
        return output_path
        
    finally:
        driver.quit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture captcha from SAT certificate recovery page."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Target URL (defaults to SAT recovery page).",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for captcha image.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Page load timeout in seconds.",
    )
    args = parser.parse_args(argv)
    
    try:
        capture_captcha(args.url, args.output, args.timeout)
        return 0
    except Exception as exc:
        print(f"Error capturing captcha: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

