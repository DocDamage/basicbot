"""Add Selenium/Playwright support for JavaScript-rendered sites"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Check if selenium/playwright are installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Install with: pip install selenium")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install")

# Template for adding browser automation to extractors
BROWSER_DOWNLOAD_TEMPLATE = '''
    def _download_with_browser(self, url: str) -> Optional[Path]:
        """Download using browser automation for JavaScript-rendered sites"""
        if not SELENIUM_AVAILABLE and not PLAYWRIGHT_AVAILABLE:
            print("    ⚠️  Browser automation not available. Install selenium or playwright.")
            return None
        
        try:
            # Try Playwright first (more reliable)
            if PLAYWRIGHT_AVAILABLE:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until='networkidle')
                    
                    # Wait for content to load
                    page.wait_for_timeout(2000)
                    
                    # Get page content
                    html_content = page.content()
                    browser.close()
                    
                    raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
                    raw_file.write_text(html_content, encoding='utf-8')
                    print(f"    ✓ Downloaded with Playwright to {raw_file.name}")
                    return raw_file
            
            # Fallback to Selenium
            elif SELENIUM_AVAILABLE:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                
                # Wait for content
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                html_content = driver.page_source
                driver.quit()
                
                raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
                raw_file.write_text(html_content, encoding='utf-8')
                print(f"    ✓ Downloaded with Selenium to {raw_file.name}")
                return raw_file
                
        except Exception as e:
            print(f"    ⚠️  Browser automation error: {e}")
            return None
'''

print("=" * 70)
print("BROWSER AUTOMATION SUPPORT")
print("=" * 70)
print()
print(f"Selenium available: {SELENIUM_AVAILABLE}")
print(f"Playwright available: {PLAYWRIGHT_AVAILABLE}")
print()

if not SELENIUM_AVAILABLE and not PLAYWRIGHT_AVAILABLE:
    print("To enable browser automation:")
    print("  pip install selenium playwright")
    print("  playwright install")
    print()
    print("Then extractors can use browser automation for JavaScript-rendered sites.")
else:
    print("✓ Browser automation is available!")
    print("  Extractors can be enhanced to use browser automation.")
    print("  See BROWSER_DOWNLOAD_TEMPLATE above for implementation.")

print()
print("=" * 70)

