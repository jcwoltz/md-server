#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os
import re
import glob
import tempfile
import urllib.parse
from datetime import datetime

SERVE_DIR = '/srv'
STYLES_DIR = '/app'


def resolve_wiki_links(content, file_path, srv_dir):
    """Convert Obsidian [[wiki links]] to markdown links, resolved against the vault."""
    file_dir = os.path.dirname(file_path)

    def replace_link(m):
        inner = m.group(1)

        # Split on | for display text: [[target|label]] or [[target]]
        if '|' in inner:
            target_part, display = inner.split('|', 1)
        else:
            target_part = inner
            display = None

        # Split on # for section anchors: [[file#heading]]
        if '#' in target_part:
            filename, section = target_part.split('#', 1)
            anchor = '#' + re.sub(r'\s+', '-', section.strip().lower())
        else:
            filename = target_part
            anchor = ''

        filename = filename.strip()
        label = display.strip() if display else target_part.strip()

        if not filename:
            return f'[{label}]({anchor})'

        # 1. Same directory
        same_dir = os.path.join(file_dir, filename + '.md')
        if os.path.exists(same_dir):
            url = '/' + os.path.relpath(same_dir, srv_dir).replace(os.sep, '/')
            return f'[{label}]({url}{anchor})'

        # 2. Recursive search (exact name)
        matches = glob.glob(os.path.join(srv_dir, '**', filename + '.md'), recursive=True)

        # 3. Case-insensitive fallback
        if not matches:
            target_lower = (filename + '.md').lower()
            matches = [
                f for f in glob.glob(os.path.join(srv_dir, '**', '*.md'), recursive=True)
                if os.path.basename(f).lower() == target_lower
            ]

        if matches:
            matches.sort(key=len)  # prefer shortest (least-nested) path
            url = '/' + os.path.relpath(matches[0], srv_dir).replace(os.sep, '/')
            return f'[{label}]({url}{anchor})'

        # Not found — render as struck-through text with tooltip
        return f'<span class="wiki-link-missing" title="Not found: {filename}">{label}</span>'

    return re.sub(r'\[\[([^\]]+?)\]\]', replace_link, content)


class PandocHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # Strip known suffixes in any order
        break_mode = False
        toc_mode = False
        compact_mode = False
        changed = True
        while changed:
            changed = False
            if path.endswith('.break'):
                path = path[:-6]
                break_mode = True
                changed = True
            elif path.endswith('.toc'):
                path = path[:-4]
                toc_mode = True
                changed = True
            elif path.endswith('.compact'):
                path = path[:-8]
                compact_mode = True
                changed = True

        if not path.endswith('.md'):
            self.send_error(404, 'Not a markdown file')
            return

        # Prevent path traversal
        real_srv = os.path.realpath(SERVE_DIR)
        file_path = os.path.realpath(os.path.join(real_srv, path.lstrip('/')))
        if not file_path.startswith(real_srv + os.sep):
            self.send_error(403, 'Forbidden')
            return

        if not os.path.isfile(file_path):
            self.send_error(404, 'File not found')
            return

        # Read and preprocess
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = resolve_wiki_links(content, file_path, real_srv)

        # Doc-meta footer
        mtime = os.path.getmtime(file_path)
        modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        generated = datetime.now().strftime('%Y-%m-%d %H:%M')
        filename = os.path.basename(file_path)
        footer_html = (
            f'<div class="doc-meta">'
            f'Source: {filename} | Modified: {modified} | Generated: {generated}'
            f'</div>'
        )

        # DRAFT watermark from frontmatter
        is_draft = bool(re.search(r'^status:\s*DRAFT', content, re.MULTILINE | re.IGNORECASE))

        if compact_mode:
            style_name = 'compact.html'
        elif break_mode:
            style_name = 'break.html'
        else:
            style_name = 'nobreak.html'
        style_file = os.path.join(STYLES_DIR, style_name)
        tmp_files = []

        try:
            # Preprocessed content as temp .md
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(content)
                content_tmp = f.name
            tmp_files.append(content_tmp)

            # Footer temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(footer_html)
                footer_tmp = f.name
            tmp_files.append(footer_tmp)

            cmd = [
                'pandoc', content_tmp,
                '-f', 'gfm+hard_line_breaks',
                '-t', 'html5',
                '--standalone',
                '--syntax-highlighting=kate',
                '--lua-filter=/app/callouts.lua',
                f'--resource-path={os.path.dirname(file_path)}',
                f'--include-in-header={style_file}',
            ]

            if is_draft:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write('<div class="draft-watermark">DRAFT</div>')
                    draft_tmp = f.name
                tmp_files.append(draft_tmp)
                cmd.append(f'--include-before-body={draft_tmp}')

            if toc_mode:
                cmd += ['--toc', '--toc-depth=3', '--metadata=toc-title:Contents']

            cmd += [
                f'--include-after-body={footer_tmp}',
                '--include-after-body=/app/copycode.html',
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

        finally:
            for f in tmp_files:
                try:
                    os.unlink(f)
                except Exception:
                    pass

        if result.returncode != 0:
            self.send_error(500, f'Pandoc error: {result.stderr}')
            return

        html = result.stdout.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        print(f'{self.address_string()} - {format % args}', flush=True)


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 3000), PandocHandler)
    print('Pandoc sidecar listening on :3000', flush=True)
    server.serve_forever()
