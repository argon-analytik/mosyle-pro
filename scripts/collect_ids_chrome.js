(async()=>{
  const a='.article.section > .arrow, span.chevron';
  for(;;){
    const c=[...document.querySelectorAll(a)]
      .filter(e=>!e.parentElement.classList.contains('showing_children')&&!e.closest('[data-open="true"]'));
    if(!c.length) break; c.forEach(e=>e.click());
    await new Promise(r=>setTimeout(r,200));
  }
  const ids=[...document.querySelectorAll('[data-article-id],[onclick*="viewArticle"]')]
    .map(el=>el.dataset.articleId||(el.getAttribute('onclick').match(/,\s*(\d+)\)/)||[])[1])
    .filter(Boolean);
  copy(JSON.stringify(ids,null,2));
})();
