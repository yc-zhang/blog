# 个人文档

旧文档案。Markdown 原稿按主题存放在 `content/`。

- [技术文章](content/technical/) 按一级分类和二级主题组织。[文章目录](content/technical/catalog.json)
- [个人感悟](content/personal/reflections/) 保存在本仓库。

新增技术文章时，将 Markdown 放到对应的二级主题目录，并在 `content/technical/catalog.json` 中登记标题和文件名（省略 `.md`）。本地预览只读取 `content/technical/`，输出到 `dist/`。

本地预览需要 Python 3.12 或更新版本：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_pages.py
.venv/bin/python -m http.server --directory dist 8000
```

打开 [本地站点](http://localhost:8000)。正文中的原站图片仍使用原有远程链接。
