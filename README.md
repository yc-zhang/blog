# Yuchen 的技术博客

[浏览技术博客](https://yc-zhang.github.io/blog/)。内容覆盖软件架构、编程语言、数据库、Web 与网络、安全。

## 写作与发布

技术文章按两级主题存放在 [content/technical](content/technical/)。新增文章时，在对应主题目录添加 Markdown，并在 [catalog.json](content/technical/catalog.json) 登记标题与文件名（省略 `.md`）。文章插图存放于同级的 `images/<文章文件名>/`，正文使用相对路径引用。

推送到 `main` 后，GitHub Actions 构建并发布 GitHub Pages。这个仓库只收录技术文章。

## 本地预览

使用 Python 3.12 或更新版本。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_pages.py
.venv/bin/python -m http.server --directory dist 8000
```

打开 [本地预览](http://localhost:8000)。
