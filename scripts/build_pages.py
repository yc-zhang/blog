from html import escape
import json
from pathlib import Path
import re
import shutil

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'content' / 'technical'
OUTPUT = ROOT / 'dist'
AUTHOR = 'Yuchen'
SITE_NAME = f'{AUTHOR} 的技术博客'
REPOSITORY = 'https://github.com/yc-zhang/blog'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
IMAGE_EXTENSIONS = {'.avif', '.gif', '.jpeg', '.jpg', '.png', '.webp'}
STATIC_FILES = ('style.css', 'site.js')
FEATURED_ARTICLE = Path('architecture/microservices/choosing-service-discovery.html')
FEATURED_IMAGE = Path('architecture/microservices/images/choosing-service-discovery/02.png')


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


def document(title, home, body, description=None):
    page_title = SITE_NAME if title == SITE_NAME else f'{title} · {SITE_NAME}'
    description_tag = (
        f'<meta name="description" content="{escape(description)}">' if description else ''
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{escape(page_title)}</title>
  {description_tag}
  <link rel="stylesheet" href="{home}style.css">
  <script src="{home}site.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">跳到正文</a>
  <header class="site-header">
    <div class="shell header-inner">
      <a class="brand" href="{home}index.html"><span class="brand-mark" aria-hidden="true"></span>{AUTHOR}</a>
      <nav aria-label="主导航">
        <a href="{home}index.html#library">文章目录</a>
        <a href="{REPOSITORY}">GitHub<span aria-hidden="true"> ↗</span></a>
      </nav>
    </div>
  </header>
  {body}
  <footer class="shell site-footer"><span>{SITE_NAME}</span><a href="#main">返回顶部 ↑</a></footer>
</body>
</html>
'''


def write_page(relative, title, home, body, description=None):
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document(title, home, body, description), encoding='utf-8')


def render_article(source, title):
    raw = source.read_text(encoding='utf-8-sig').lstrip('\n')
    prefix = f'# {title}\n'
    if raw.startswith(prefix):
        raw = raw[len(prefix):].lstrip('\n')
    tokens = markdown.parse(raw)
    headings = []
    for index, token in enumerate(tokens):
        if token.type != 'heading_open':
            continue
        if token.tag == 'h1':
            token.tag = tokens[index + 2].tag = 'h2'
        if token.tag in {'h2', 'h3'}:
            heading_id = f'section-{len(headings) + 1}'
            token.attrSet('id', heading_id)
            # The inline token already holds the original heading text.
            label = ''.join(child.content for child in tokens[index + 1].children
                            if child.type in {'text', 'code_inline'})
            headings.append((heading_id, token.tag, label or tokens[index + 1].content))
    rendered = markdown.renderer.render(tokens, markdown.options, {})
    return rendered, headings


def article_images(source):
    directory = source.parent / 'images' / source.stem
    if directory.is_dir():
        for image in directory.iterdir():
            if image.is_file() and image.suffix.lower() in IMAGE_EXTENSIONS:
                if not image.resolve().is_relative_to(CONTENT.resolve()):
                    raise ValueError(f'Invalid article image: {image}')
                yield image.relative_to(CONTENT)


def article_page(title, category_id, category_title, anchor, topic_title, body, headings):
    toc = ''
    if len(headings) >= 2:
        links = ''.join(f'<li class="{level}"><a href="#{heading_id}">{escape(label)}</a></li>'
                        for heading_id, level, label in headings)
        toc = f'''<aside class="article-aside"><details class="toc" open>
                     <summary>本文目录</summary><nav aria-label="章节"><ul>{links}</ul></nav>
                   </details></aside>'''
    return f'''
      <main id="main" class="shell reading">
        <nav class="breadcrumbs" aria-label="当前位置">
          <a href="../../index.html#library">文章目录</a><span aria-hidden="true">/</span>
          <a href="../../index.html#{category_id}">{category_title}</a><span aria-hidden="true">/</span>
          <a href="../../index.html#{anchor}">{topic_title}</a>
        </nav>
        <header class="article-heading"><h1>{escape(title)}</h1></header>
        <div class="reading-layout">
          {toc}
          <article class="prose">{body}</article>
        </div>
        <a class="back-link" href="../../index.html#{anchor}">← 返回{topic_title}</a>
      </main>'''


def index_page(nav, categories, count, featured_title):
    featured = ''
    if featured_title:
        featured = f'''
          <a class="feature" href="{FEATURED_ARTICLE.as_posix()}">
            <div class="feature-visual">
              <img src="{FEATURED_IMAGE.as_posix()}" width="543" height="405" alt="">
            </div>
            <div class="feature-body"><div><span>推荐阅读 · 微服务</span>
              <strong>{escape(featured_title)}</strong></div><span class="feature-arrow" aria-hidden="true">↗</span>
            </div>
          </a>'''
    return f'''
      <main id="main">
        <section class="hero">
          <div class="shell hero-inner">
            <div class="hero-copy">
              <h1>技术博客<span aria-hidden="true">.</span></h1>
              <p>记录软件设计、技术选型与工程实践。</p>
              <a class="hero-link" href="#library">浏览文章 <span aria-hidden="true">↓</span></a>
            </div>
            {featured}
          </div>
        </section>
        <section class="shell library" id="library" aria-labelledby="library-title">
          <div class="library-head">
            <div><h2 id="library-title">文章目录</h2><p id="result-count" role="status" aria-live="polite">{count} 篇文章</p></div>
            <div class="search" id="search" hidden>
              <label class="sr-only" for="article-search">搜索文章</label>
              <input id="article-search" type="search" placeholder="搜索标题或主题" autocomplete="off">
            </div>
          </div>
          <nav class="category-nav" aria-label="一级分类">{''.join(nav)}</nav>
          <p class="no-results" id="no-results" hidden>没有匹配的文章。试试其他关键词。</p>
          {''.join(categories)}
        </section>
      </main>'''


def build():
    if (ROOT / 'content' / 'personal').exists():
        raise ValueError('This repository only accepts technical articles under content/technical.')
    catalog = json.loads((CONTENT / 'catalog.json').read_text(encoding='utf-8'))
    listed = set()
    nav = []
    categories = []
    pages = []
    images = set()
    used_categories = set()
    featured_title = None
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
                body, headings = render_article(source, title)
                images.update(article_images(source))
                page = article_page(title, category_id, category_title, anchor, topic_title, body, headings)
                pages.append((output, title, page))
                if output == FEATURED_ARTICLE:
                    featured_title = title
            topic_blocks.append(f'<section class="topic" id="{anchor}"><h4>{topic_title}</h4>'
                                f'<ul>{"".join(article_links)}</ul></section>')
        categories.append(f'<section class="category" id="{category_id}"><h3>{category_title}</h3>'
                          f'<div class="topics">{"".join(topic_blocks)}</div></section>')

    sources = set(CONTENT.rglob('*.md'))
    if listed != sources:
        raise ValueError(f'Catalog must list each technical article: {sources ^ listed}')
    if featured_title and FEATURED_IMAGE not in images:
        raise ValueError(f'Featured image missing: {FEATURED_IMAGE}')
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for asset in STATIC_FILES:
        shutil.copyfile(ROOT / 'site-assets' / asset, OUTPUT / asset)
    (OUTPUT / '.nojekyll').touch()
    for image in sorted(images):
        target = OUTPUT / image
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONTENT / image, target)
    for output, title, body in pages:
        write_page(output, title, '../../', body)
    write_page(Path('index.html'), SITE_NAME, './', index_page(nav, categories, len(pages), featured_title),
               f'{AUTHOR} 的技术文章，按软件架构、编程语言、数据库、Web 与网络、安全分类。')
    print(f'Built {len(pages)} articles and {len(images)} images in {OUTPUT}')


if __name__ == '__main__':
    build()
