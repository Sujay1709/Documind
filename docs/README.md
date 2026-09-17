# DocuMind visuals

The README uses lightweight SVG visuals that match the current orange-futuristic
web app. Keep these assets in vector form so documentation stays small and sharp.

| File | Use |
| --- | --- |
| `landing.svg` | Workspace upload and empty state. |
| `chat.svg` | Grounded chat with expandable Sources panel. |

## How to regenerate

These mockups are authored as `landing.svg` and `chat.svg` so they're easy to
tweak in any vector editor without capturing sensitive documents.

```bash
python -c "import cairosvg; cairosvg.svg2png(url='landing.svg', write_to='landing.png', output_width=1536); cairosvg.svg2png(url='chat.svg', write_to='chat.png', output_width=1536)"
```

## How to capture real screenshots

For an authentic screenshot of the running app:

1. Start the app: `ollama serve &` then `streamlit run src/documind/app.py`.
2. Open `http://localhost:8501`, upload a PDF (e.g. `ai-fluency-summary.pdf`),
   ask a question, and let the streamed answer finish.
3. Use the browser's screenshot tool or Playwright:
   ```python
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page(viewport={"width": 1440, "height": 900})
       page.goto("http://localhost:8501")
       page.screenshot(path="/tmp/documind-landing.png", full_page=False)
   ```
4. Keep real screenshots outside the repository unless they are intentionally
   sanitized and approved for public sharing.

The SVG versions stay as the fallback so the README is never broken when the
app isn't running.
