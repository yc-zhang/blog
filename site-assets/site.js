const search = document.querySelector('#article-search');

if (search) {
  document.querySelector('#search').hidden = false;
  const normalize = (value) => value.normalize('NFKC').toLocaleLowerCase();
  const categories = [...document.querySelectorAll('.category')].map((category) => {
    const categoryName = category.querySelector('h3').textContent;
    const topics = [...category.querySelectorAll('.topic')].map((topic) => {
      const topicName = topic.querySelector('h4').textContent;
      const entries = [...topic.querySelectorAll('li')].map((row) => ({
        row,
        terms: normalize([row.textContent, topicName, categoryName].join(' ')),
      }));
      return { topic, entries };
    });
    return { category, topics };
  });
  const resultCount = document.querySelector('#result-count');
  const emptyMessage = document.querySelector('#no-results');

  function filterArticles() {
    const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let total = 0;
    for (const { category, topics } of categories) {
      for (const { topic, entries } of topics) {
        for (const { row, terms } of entries) {
          row.hidden = !words.every((word) => terms.includes(word));
          if (!row.hidden) total += 1;
        }
        topic.hidden = entries.every(({ row }) => row.hidden);
      }
      category.hidden = topics.every(({ topic }) => topic.hidden);
    }
    resultCount.textContent = words.length ? `找到 ${total} 篇文章` : `${total} 篇文章`;
    emptyMessage.hidden = total !== 0;
  }

  search.addEventListener('input', filterArticles);
  document.querySelector('.category-nav').addEventListener('click', (event) => {
    if (event.target.closest('a') && search.value) {
      search.value = '';
      filterArticles();
    }
  });
  filterArticles();
}

if (matchMedia('(max-width: 680px)').matches) {
  document.querySelector('.toc')?.removeAttribute('open');
}

if (navigator.clipboard) {
  for (const code of document.querySelectorAll('.prose pre > code')) {
    const frame = document.createElement('div');
    const pre = code.parentElement;
    const button = document.createElement('button');
    frame.className = 'code-frame';
    button.type = 'button';
    button.className = 'copy-code';
    button.textContent = '复制';
    button.setAttribute('aria-label', '复制代码');
    button.setAttribute('aria-live', 'polite');
    pre.before(frame);
    frame.append(pre, button);
    let reset;
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = '已复制';
        button.setAttribute('aria-label', '已复制代码');
      } catch {
        button.textContent = '复制失败';
        button.setAttribute('aria-label', '复制代码失败');
      }
      clearTimeout(reset);
      reset = setTimeout(() => {
        button.textContent = '复制';
        button.setAttribute('aria-label', '复制代码');
      }, 1800);
    });
  }
}
