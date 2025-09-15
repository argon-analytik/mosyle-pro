(()=>{
  const ids=[...document.querySelectorAll('[data-article-id],[onclick*="viewArticle"]')]
    .map(el=>el.dataset.articleId||(el.getAttribute('onclick').match(/,\s*(\d+)\)/)||[])[1])
    .filter(Boolean);
  console.log(JSON.stringify(ids,null,2));
})();
