# Xray Decky — Public Plugin Page

Static landing page for the Xray Decky plugin. Mobile-first, Steam Deck–style, responsive (375px–1280px).

## Publish on GitHub Pages

1. **Settings** → **Pages** → **Source**: Deploy from a branch  
2. **Branch**: `main` (or your default branch)  
3. **Folder**: `/docs`

The page will be available at:
**https://&lt;owner&gt;.github.io/xray-decky/**

## Preview locally

```bash
cd docs && python3 -m http.server 8765
# Open http://localhost:8765
```

Or open `index.html` directly in a browser.

## Edit

- `index.html` — content, sections, image references  
- `styles/main.css` — layout, colors, typography  
- `assets/` — hero and feature images  

## More

See [specs/004-plugin-public-page/quickstart.md](../specs/004-plugin-public-page/quickstart.md) for full documentation.
