# 个人文档

旧文档案。Markdown 原稿按主题存放在 `content/`。

- [技术文章](content/technical/) 按一级分类和二级主题组织。[文章目录](content/technical/catalog.json)
- [个人感悟](content/personal/reflections/) 保存在本仓库。

[技术文章站](https://yc-zhang.github.io/technical-articles/) 由 [technical-articles 发布仓库](https://github.com/yc-zhang/technical-articles) 的 `main` 分支托管。构建只读取 `content/technical/`，并将静态页面输出到 `dist/`。

新增技术文章时，将 Markdown 放到对应的二级主题目录，在 `content/technical/catalog.json` 中登记标题和文件名（省略 `.md`），并提交本仓库。重新构建后，将整个 `dist/` 的内容同步至专用发布仓库，再提交和推送发布仓库的 `main`。发布仓库仅存放生成的站点文件。

本地预览需要 Python 3.12 或更新版本：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build_pages.py
.venv/bin/python -m http.server --directory dist 8000
```

打开 [本地站点](http://localhost:8000)。正文中的原站图片仍使用原有远程链接。
