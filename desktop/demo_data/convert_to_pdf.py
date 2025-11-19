"""
Convert HTML leases to PDF using Playwright
"""
import asyncio
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

async def html_to_pdf(html_path, pdf_path):
    """Convert single HTML to PDF"""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Load HTML
            await page.goto(f"file:///{html_path.as_posix()}")

            # Generate PDF
            await page.pdf(path=str(pdf_path), format='Letter')

            await browser.close()

        print(f"Converted: {pdf_path.name}")
        return True
    except Exception as e:
        print(f"Error converting {html_path.name}: {e}")
        return False

async def main():
    """Convert all HTML files to PDF"""
    script_dir = Path(__file__).parent

    html_files = list(script_dir.glob("lease_*_UNREDACTED.html"))

    if not html_files:
        print("No HTML files found!")
        return

    print(f"\nConverting {len(html_files)} HTML files to PDF...")
    print("=" * 60)

    for html_file in sorted(html_files):
        pdf_file = html_file.with_suffix('.pdf')
        await html_to_pdf(html_file, pdf_file)

    print(f"\nAll PDFs created in: {script_dir}")
    print("\nNext: Open the app and redact lease_01_UNREDACTED.pdf")

if __name__ == "__main__":
    asyncio.run(main())
