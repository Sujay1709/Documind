# DocuMind screenshots

Place PNGs here for the README and any external sharing.

| File | Use |
| --- | --- |
| `landing.png` | Top of README / project page — empty-state hero. |
| `chat.png` | Mid-README — chat with expandable Sources panel. |

## How to regenerate

These mockups are baked from `landing.svg` and `chat.svg` so they're easy to
tweak in any vector editor without re-running a model.

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
       page.screenshot(path="docs/landing.png", full_page=False)
   ```
4. Replace the SVG-baked mockups if you want the README to show *real* runs.

The SVG versions stay as the fallback so the README is never broken when the
app isn't running.
