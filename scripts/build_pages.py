from html import escape
import json
from pathlib import Path
import re
import shutil

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content' / 'technical'
OUTPUT = ROOT / 'dist'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
IMAGE_EXTENSIONS = {'.avif', '.gif', '.jpeg', '.jpg', '.png', '.webp'}


def slug(entry):
    value = entry['slug']
    if not SLUG.fullmatch(value):
        raise ValueError(f'Invalid catalog slug: {value!r}')
    return value


def safe_inline_html(self, tokens, idx, options, env):
    value = tokens[idx].content
    if value in {'<strong>', '</strong>'}:
        return value
    return escape(value)


def escape_html_block(self, tokens, idx, options, env):
    return f'<pre>{escape(tokens[idx].content)}</pre>\n'


markdown = MarkdownIt('commonmark', {'html': True}).enable('table')
markdown.add_render_rule('html_inline', safe_inline_html)
markdown.add_render_rule('html_block', escape_html_block)


def document(title, home, body):
    name = '张羽辰的技术文章'
    page_title = name if title == name else f'{title} · {name}'
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page_title)}</title>
  <link rel="stylesheet" href="{home}style.css">
</head>
<body>
  <header class="site-header"><a href="{home}index.html">{name}</a></header>
  {body}
</body>
</html>
'''


def write_page(relative, title, home, body):
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document(title, home, body), encoding='utf-8')


def render_article(source, title):
    raw = source.read_text(encoding='utf-8-sig').lstrip('\n')
    # Archived web articles already carry their title above their source line.
    prefix = f'# {title}\n'
    if raw.startswith(prefix):
        raw = raw[len(prefix):].lstrip('\n')
    return markdown.render(raw)


def article_images(source):
    directory = source.parent / 'images' / source.stem
    if directory.is_dir():
        for image in directory.iterdir():
            if image.is_file() and image.suffix.lower() in IMAGE_EXTENSIONS:
                if not image.resolve().is_relative_to(CONTENT.resolve()):
                    raise ValueError(f'Invalid article image: {image}')
                yield image.relative_to(CONTENT)


def build():
    catalog = json.loads((CONTENT / 'catalog.json').read_text(encoding='utf-8'))
    listed = set()
    nav = []
    categories = []
    pages = []
    images = set()
    used_categories = set()
    for category in catalog:
        category_id = slug(category)
        if category_id in used_categories:
            raise ValueError(f'Duplicate category: {category_id}')
        used_categories.add(category_id)
        category_title = escape(category['title'])
        nav.append(f'<a href="#{category_id}">{category_title}</a>')
        topic_blocks = []
        used_topics = set()
        for topic in category['topics']:
            topic_id = slug(topic)
            if topic_id in used_topics:
                raise ValueError(f'Duplicate topic: {category_id}/{topic_id}')
            used_topics.add(topic_id)
            topic_title = escape(topic['title'])
            anchor = f'{category_id}-{topic_id}'
            article_links = []
            for article in topic['articles']:
                title = article['title']
                relative = Path(category_id, topic_id, slug(article))
                source = (CONTENT / relative).with_suffix('.md')
                if source in listed or not source.resolve().is_relative_to(CONTENT.resolve()):
                    raise ValueError(f'Invalid catalog source: {source}')
                listed.add(source)
                output = relative.with_suffix('.html')
                article_links.append(f'<li><a href="{output.as_posix()}">{escape(title)}</a></li>')
                body = render_article(source, title)
                images.update(article_images(source))
                pages.append((output, title, f'''
                  <main class="reading">
                    <nav class="breadcrumbs" aria-label="当前位置">
                      <a href="../../index.html#{category_id}">{category_title}</a>
                      <span aria-hidden="true">/</span>
                      <a href="../../index.html#{anchor}">{topic_title}</a>
                    </nav>
                    <article><h1>{escape(title)}</h1>{body}</article>
                    <a class="return" href="../../index.html#{anchor}">返回{topic_title}</a>
                  </main>'''))
            topic_blocks.append(f'<section class="topic" id="{anchor}"><h3>{topic_title}</h3>'
                                f'<ul>{"".join(article_links)}</ul></section>')
        categories.append(f'<section class="category" id="{category_id}"><h2>{category_title}</h2>'
                          f'<div class="topics">{"".join(topic_blocks)}</div></section>')

    sources = set(CONTENT.rglob('*.md'))
    if listed != sources:
        raise ValueError(f'Catalog must list each technical article: {sources ^ listed}')
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copyfile(ROOT / 'site-assets' / 'style.css', OUTPUT / 'style.css')
    (OUTPUT / '.nojekyll').touch()
    for image in sorted(images):
        target = OUTPUT / image
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONTENT / image, target)
    for output, title, body in pages:
        write_page(output, title, '../../', body)
    write_page(Path('index.html'), '张羽辰的技术文章', './', f'''
      <main class="directory">
        <div class="intro"><h1>技术文章</h1><p>{len(pages)} 篇文章，按主题浏览。</p></div>
        <nav class="category-nav" aria-label="文章分类">{"".join(nav)}</nav>
        {"".join(categories)}
      </main>''')
    print(f'Built {len(pages)} articles in {OUTPUT}')


if __name__ == '__main__':
    build()
