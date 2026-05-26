from playwright.sync_api import Playwright
from src.shared.constants import URL


def abrir_site(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False, slow_mo=300, args=["--start-maximized"])
    context = browser.new_context(viewport=None,accept_downloads=True)
    page = context.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    return browser, context, page