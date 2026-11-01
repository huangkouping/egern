/**
 * Egern Script: 移动端搜索自动翻页 (Baidu & Google)
 * 拦截百度和 Google 的搜索 HTML，在 </body> 前注入客户端无限滚动逻辑
 */

const $ = typeof $response !== 'undefined' ? $response : null;

if ($ && $.body) {
    let html = $.body;

    const injectClientScript = `
<script>
(function() {
    let isLoading = false;
    let page = 1;
    const host = window.location.hostname;
    const isGoogle = /^www\.google\.(?:com|[a-z]{2,3}|com\.[a-z]{2}|co\.[a-z]{2})$/.test(host);
    const isBaidu = host === 'm.baidu.com' || host === 'www.baidu.com';
    if (!isGoogle && !isBaidu) return;

    function getQueryParam(param) {
        return new URLSearchParams(window.location.search).get(param) || '';
    }

    const queryWord = isGoogle
        ? getQueryParam('q')
        : (getQueryParam('word') || getQueryParam('wd'));
    if (!queryWord) return;

    const config = isGoogle ? {
        getContainer: () => document.querySelector('#rso') || document.querySelector('#center_col') || document.body,
        cardSelector: '#rso > div.MjjYud, #rso > div.g, #rso > div',
        hideSelectors: '#botstuff, #navcnt, #footer',
        getUrl: (p) => {
            const url = new URL(window.location.href);
            url.searchParams.set('start', String(p * 10));
            return url.toString();
        }
    } : {
        getContainer: () => document.querySelector('#results') || document.querySelector('#page-bd') || document.body,
        cardSelector: '#results .c-result, #results > div, .results > div',
        hideSelectors: '#page-controller, .anchor-tag, .new-pagenav',
        getUrl: (p) => {
            const pn = p * 10;
            return window.location.origin + window.location.pathname + '?word=' + encodeURIComponent(queryWord) + '&pn=' + pn;
        }
    };

    const container = config.getContainer();
    if (!container) return;

    const hideStyle = document.createElement('style');
    hideStyle.textContent = config.hideSelectors + ' { display: none !important; }';
    document.head.appendChild(hideStyle);

    const statusDiv = document.createElement('div');
    statusDiv.id = 'egern-page-status';
    statusDiv.style.cssText = 'text-align:center;padding:16px 0;font-size:12px;color:#999;clear:both;';
    statusDiv.innerText = '滑动加载更多结果';
    container.parentNode.insertBefore(statusDiv, container.nextSibling);

    function fetchNextPage() {
        if (isLoading) return;
        isLoading = true;
        statusDiv.innerText = '正在加载下一页...';

        const targetUrl = config.getUrl(page);
        fetch(targetUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.text())
        .then(text => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const nextCards = doc.querySelectorAll(config.cardSelector);

            if (nextCards.length > 0) {
                const fragment = document.createDocumentFragment();
                const sep = document.createElement('div');
                sep.style.cssText = 'margin:14px 0 8px;padding:4px 0;border-top:1px dashed #e6e6e6;font-size:11px;color:#bbb;text-align:center;clear:both;';
                sep.textContent = '第 ' + (page + 1) + ' 页';
                fragment.appendChild(sep);

                nextCards.forEach(card => {
                    if (card.children.length > 0) {
                        fragment.appendChild(document.importNode(card, true));
                    }
                });

                container.appendChild(fragment);
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

    let scrollTimer = null;
    function checkScroll() {
        if (scrollTimer) return;
        scrollTimer = setTimeout(() => {
            scrollTimer = null;
            const scrollBottom = document.documentElement.scrollHeight - (window.innerHeight + window.scrollY);
            if (scrollBottom < 600 && !isLoading) {
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
