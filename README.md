# md-server

A self-hosted markdown rendering server using Caddy and Pandoc. Drop markdown files in a directory and browse them as styled HTML with file browsing, table of contents, callouts, code copy buttons, and print-friendly output.

## Quick Start

```bash
git clone <this-repo> md-server
cd md-server
mkdir -p docs   # put your .md files here
docker compose up -d
```

Browse to **http://localhost:8095**

## Serving a Different Directory

By default, files are served from `./docs/`. To serve markdown from elsewhere, create a `.env` file:

```
DOCS_DIR=/path/to/your/markdown
```

Or inline:

```bash
DOCS_DIR=~/notes docker compose up -d
```

## Features

### Rendering Modes

Append suffixes to any `.md` URL to change the output:

| Suffix | Effect |
|--------|--------|
| *(none)* | Default style, continuous flow |
| `.break` | Page break before each H2 (for printing) |
| `.compact` | Denser layout, smaller fonts |
| `.toc` | Adds a table of contents |

Suffixes combine: `doc.md.toc.break` gives you a TOC with page breaks.

### Callouts

GitHub-style alert syntax is supported:

```markdown
> [!NOTE]
> This renders as a styled callout box.
```

Supported types: `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`

### Wiki Links

Obsidian-style `[[wiki links]]` are resolved against the served directory. Supports `[[file]]`, `[[file|display text]]`, and `[[file#heading]]`.

### Other

- File browser for navigating directories
- Copy button on code blocks
- DRAFT watermark when frontmatter contains `status: DRAFT`
- Footer with source filename and timestamps
- Syntax highlighting via Pandoc (kate theme)

## Architecture

Two containers:

- **caddy** — serves the file browser and proxies `.md` requests to the sidecar
- **pandoc-sidecar** — a Python HTTP server that reads the markdown file, resolves wiki links, and runs Pandoc to produce styled HTML

## Changing the Port

Edit the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8095:80"  # change 8095 to whatever you want
```

## License

[Unlicense](LICENSE) — public domain. Do whatever you want with it.
