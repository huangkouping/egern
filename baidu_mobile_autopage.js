/**
 * Egern Script: 百度移动端搜索自动翻页
 * 拦截 m.baidu.com 的搜索 HTML，在 </body> 前注入客户端无限滚动逻辑
 */

const $ = typeof $response !== 'undefined' ? $response : null;

if ($ && $.body) {
    let html = $.body;

    const injectClientScript = `
<script>
(function() {
    let isLoading = false;
    let page = 1;

    // 获取当前搜索参数
    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param) || '';
    }

    const word = getQueryParam('word') || getQueryParam('wd');
    if (!word) return;

    // 状态指示条
    const statusDiv = document.createElement('div');
    statusDiv.id = 'egern-page-status';
    statusDiv.style.cssText = 'text-align:center;padding:16px 0;font-size:12px;color:#999;clear:both;';
    statusDiv.innerText = '滑动加载更多结果';

    const resultsContainer = document.querySelector('#results') || document.querySelector('#page-bd') || document.body;
    resultsContainer.appendChild(statusDiv);

    // 隐藏移动端底部的原生翻页/更多按钮，避免布局错乱
    const hideStyle = document.createElement('style');
    hideStyle.textContent = '#page-controller, .anchor-tag, .new-pagenav { display: none !important; }';
    document.head.appendChild(hideStyle);

    function fetchNextPage() {
        if (isLoading) return;
        isLoading = true;
        statusDiv.innerText = '正在加载下一页...';

        const pn = page * 10; // 百度移动端默认分页偏移量
        const targetUrl = window.location.origin + window.location.pathname + '?word=' + encodeURIComponent(word) + '&pn=' + pn;

        fetch(targetUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.text())
        .then(text => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');

            // 提取移动端搜索结果卡片
            const nextCards = doc.querySelectorAll('#results .c-result, #results > div, .results > div');
            
            if (nextCards.length > 0) {
                const fragment = document.createDocumentFragment();

                // 插入极简分页分隔线
                const sep = document.createElement('div');
                sep.style.cssText = 'margin:14px 0 8px;padding:4px 0;border-top:1px dashed #e6e6e6;font-size:11px;color:#bbb;text-align:center;';
                sep.textContent = '第 ' + (page + 1) + ' 页';
                fragment.appendChild(sep);

                nextCards.forEach(card => {
                    fragment.appendChild(document.importNode(card, true));
                });

                resultsContainer.insertBefore(fragment, statusDiv);
                page++;
                statusDiv.innerText = '滑动加载更多结果';
            } else {
                statusDiv.innerText = '没有更多搜索结果了';
                window.removeEventListener('scroll', checkScroll);
            }
            isLoading = false;
        })
        .catch(() => {
            statusDiv.innerText = '加载失败，下滑重试';
            isLoading = false;
        });
    }

    // 节流监听滑动事件
    let scrollTimer = null;
    function checkScroll() {
        if (scrollTimer) return;
        scrollTimer = setTimeout(() => {
            scrollTimer = null;
            const scrollBottom = document.documentElement.scrollHeight - (window.innerHeight + window.scrollY);
            // 距离底部 500px 时提前拉取
            if (scrollBottom < 500 && !isLoading) {
                fetchNextPage();
            }
        }, 120);
    }

    window.addEventListener('scroll', checkScroll, { passive: true });
})();
</script>
`;

    // 替换并在 </body> 前注入客户端逻辑
    if (html.includes('</body>')) {
        html = html.replace('</body>', injectClientScript + '</body>');
    } else {
        html += injectClientScript;
    }

    $done({ body: html });
} else {
    $done({});
}
