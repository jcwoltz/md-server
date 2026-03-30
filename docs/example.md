# Markdown Server

This is a test file to verify the markdown rendering server is working.

## Features

- **Pandoc rendering** with GFM support
- **Obsidian wiki links** resolved automatically
- **GitHub-style callouts** via Lua filter
- **Copy-to-clipboard** buttons on code blocks
- **Three style modes**: default, `.break` (page breaks at H2), `.compact` (denser layout)
- **Table of contents**: append `.toc` to any URL
- **DRAFT watermark**: add `status: DRAFT` in frontmatter

## Example Table

| Feature | URL suffix |
|---------|-----------|
| Default style | `file.md` |
| Page breaks at H2 | `file.md.break` |
| Compact layout | `file.md.compact` |
| With TOC | `file.md.toc` |
| Combined | `file.md.toc.break` |

## Example Callout

> [!NOTE]
> Place your markdown files in the `docs/` directory (or change `DOCS_DIR` in your `.env`).

## Example Code

```python
print("Hello from the markdown server!")
```
