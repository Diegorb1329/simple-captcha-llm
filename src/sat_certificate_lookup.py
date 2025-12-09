"""Core library for RFC certificate lookup with captcha solving."""

import csv
import re
import time
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config import (
    CAPTCHA_IMAGE_SELECTORS, RFC_INPUT_SELECTORS,
    CAPTCHA_INPUT_SELECTORS, SEARCH_BUTTON_SELECTORS, CSV_FIELDNAMES,
)
from captcha_solver import solve_captcha


class RunLogger:
    """Logger that writes to file and prints to console."""
    
    def __init__(self, run_dir: Path):
        self.log_file = run_dir / "run.log"
        self.entries = []
        self.log(f"Run started: {datetime.now().isoformat()}")
    
    def log(self, message: str):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.entries.append(entry)
        print(message)
    
    def error(self, message: str):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {message}"
        self.entries.append(entry)
        print(f"  ERROR: {message}")
    
    def save(self):
        self.log(f"Run completed: {datetime.now().isoformat()}")
        self.log_file.write_text("\n".join(self.entries), encoding="utf-8")


def create_driver() -> webdriver.Chrome:
    """Create headless Chrome WebDriver."""
    options = Options()
    for arg in ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", 
                "--disable-gpu", "--window-size=1920,1080",
                "--ignore-certificate-errors", "--ignore-ssl-errors"]:
        options.add_argument(arg)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0")
    return webdriver.Chrome(options=options)


def _find_element(driver, selectors, check_displayed=True):
    """Find first matching element from selector list."""
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el and (not check_displayed or el.is_displayed()):
                return el
        except Exception:
            pass
    return None


def _is_results_page(html: str) -> bool:
    return BeautifulSoup(html, "html.parser").find("form", id="resultados") is not None


def lookup_rfc(driver, rfc: str, url: str, run_dir: Path, logger: RunLogger, max_retries: int = 5):
    """Look up certificates for an RFC with retry logic."""
    captchas_dir = run_dir / "captchas"
    captchas_dir.mkdir(parents=True, exist_ok=True)
    
    last_captcha = None
    
    for attempt in range(max_retries):
        if attempt > 0:
            logger.log(f"  Retry {attempt}/{max_retries-1}...")
        
        driver.get(url)
        time.sleep(2)
        
        # Click 'Regresar' if on results page
        try:
            btn = driver.find_element(By.XPATH, "//input[@value='Regresar']")
            btn.click()
            time.sleep(2)
        except Exception:
            pass
        
        # Find and capture captcha
        captcha_el = _find_element(driver, CAPTCHA_IMAGE_SELECTORS, check_displayed=False)
        if not captcha_el:
            logger.log("  Warning: No captcha found")
            continue
        
        last_captcha = captcha_el.screenshot_as_png
        
        # Save captcha image
        captcha_path = captchas_dir / f"{rfc}_attempt{attempt+1}.png"
        captcha_path.write_bytes(last_captcha)
        
        # Solve captcha
        logger.log("  Solving captcha...")
        solution = solve_captcha(last_captcha)
        logger.log(f"  Solution: {solution}")
        
        # Fill form
        rfc_input = _find_element(driver, RFC_INPUT_SELECTORS)
        captcha_input = _find_element(driver, CAPTCHA_INPUT_SELECTORS)
        search_btn = _find_element(driver, SEARCH_BUTTON_SELECTORS)
        
        if not all([rfc_input, captcha_input, search_btn]):
            logger.log("  Warning: Missing form elements")
            continue
        
        rfc_input.clear()
        rfc_input.send_keys(rfc)
        captcha_input.clear()
        captcha_input.send_keys(solution)
        search_btn.click()
        time.sleep(3)
        
        html = driver.page_source
        if _is_results_page(html):
            logger.log("  ✓ Success")
            return html, last_captcha
        logger.log("  ✗ Captcha incorrect")
    
    logger.error(f"{rfc}: All {max_retries} captcha attempts failed")
    return driver.page_source, last_captcha


def parse_certificates(html: str, rfc: str) -> list[dict]:
    """Parse certificates from result HTML."""
    def empty_cert(estado):
        return {"rfc": rfc, "razon_social": "", "numero_serie": "", "estado": estado,
                "tipo": "", "fecha_inicial": "", "fecha_final": "", "url_certificado": ""}
    
    if not _is_results_page(html):
        return [empty_cert("CAPTCHA_ERROR")]
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract company name
    razon_social = ""
    table = soup.find("table", {"width": "100%"})
    if table:
        for label in table.find_all("label", class_="campos"):
            text = label.get_text(strip=True)
            if text and text != rfc and len(text) > 10 and "código" not in text.lower():
                razon_social = text
                break
    
    # Parse certificate rows
    tbody = soup.find("tbody", id=re.compile(r"tablaCert:tbn"))
    if not tbody:
        cert = empty_cert("SIN CERTIFICADOS")
        cert["razon_social"] = razon_social
        return [cert]
    
    certs = []
    for row in tbody.find_all("tr"):
        cells = row.find_all("div", class_="rf-edt-c-cnt")
        if len(cells) >= 5:
            link = cells[0].find("a")
            certs.append({
                "rfc": rfc,
                "razon_social": razon_social,
                "numero_serie": link.get_text(strip=True) if link else cells[0].get_text(strip=True),
                "estado": cells[1].get_text(strip=True),
                "tipo": cells[2].get_text(strip=True),
                "fecha_inicial": cells[3].get_text(strip=True),
                "fecha_final": cells[4].get_text(strip=True),
                "url_certificado": link.get("href", "") if link else ""
            })
    
    return certs or [{"rfc": rfc, "razon_social": razon_social, "numero_serie": "",
                      "estado": "SIN CERTIFICADOS", "tipo": "", "fecha_inicial": "",
                      "fecha_final": "", "url_certificado": ""}]


def process_rfcs(input_path: Path, output_dir: Path, url: str):
    """Process all RFCs from CSV."""
    # Create run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    logger = RunLogger(run_dir)
    logger.log(f"Run folder: {run_dir}")
    logger.log(f"Input file: {input_path}")
    
    with open(input_path, newline="", encoding="utf-8") as f:
        rfcs = list(csv.DictReader(f))
    
    logger.log(f"Processing {len(rfcs)} RFC(s)\n")
    
    all_certs = []
    driver = create_driver()
    
    try:
        for i, row in enumerate(rfcs, 1):
            rfc = row.get("rfc", "").strip()
            if not rfc:
                continue
            
            logger.log(f"[{i}] {rfc}")
            try:
                html, _ = lookup_rfc(driver, rfc, url, run_dir, logger)
                certs = parse_certificates(html, rfc)
                all_certs.extend(certs)
                
                for c in certs:
                    icon = "✓" if c["estado"] == "Activo" else "○"
                    logger.log(f"    {icon} {c['numero_serie']} - {c['estado']}")
                    
            except Exception as e:
                logger.error(f"{rfc}: {e}")
                all_certs.append({"rfc": rfc, "razon_social": "", "numero_serie": "",
                                  "estado": f"ERROR: {e}", "tipo": "", "fecha_inicial": "",
                                  "fecha_final": "", "url_certificado": ""})
            logger.log("")
            if i < len(rfcs):
                time.sleep(2)
    finally:
        driver.quit()
    
    # Save results CSV
    if all_certs:
        csv_path = run_dir / "resultados.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(all_certs)
        logger.log(f"Results: {csv_path} ({len(all_certs)} records)")
    
    # Save log
    logger.save()
    print(f"\nAll files saved to: {run_dir}")
