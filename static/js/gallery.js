// 将懒加载功能封装为全局函数，以便在AJAX导航时可以重新初始化
    function initLazyLoading() {
        let page = 1;
        let isLoading = false;
        let hasNext = true;
        const masonryGrid = document.getElementById('masonry-grid');
        
        // 如果元素不存在，说明不在当前页面，直接返回
        if (!masonryGrid) return;
        
        // 检查当前页面是哪个按钮
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadFollowingMoreBtn = document.getElementById('loadfollowing-more-btn');
        const activeBtn = loadMoreBtn || loadFollowingMoreBtn;
        
        const loadingSpinner = document.getElementById('loading-spinner');
        const loadMoreContainer = document.getElementById('load-more-container');
        
        // 初始化加载更多按钮显示状态
        function initLoadMore() {
            if (hasNext) {
                loadMoreContainer.style.display = 'block';
            } else {
                loadMoreContainer.style.display = 'none';
            }
        }
        
        // 加载更多相册
        function loadMoreAlbums() {
            if (isLoading || !hasNext) return;
            
            isLoading = true;
            activeBtn.style.display = 'none';
            loadingSpinner.style.display = 'inline-block';
            
            // 根据按钮类型确定URL
            let url;
            if (loadMoreBtn) {
                url = `{% url 'photos:gallery' %}?action=load_more&page=${page + 1}`;
            } else if (loadFollowingMoreBtn) {
                url = `{% url 'photos:following_albums' %}?action=load_more&page=${page + 1}`;
            }
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.html) {
                    // 将新内容添加到瀑布流容器中
                    masonryGrid.insertAdjacentHTML('beforeend', data.html);
                    
                    page = data.next_page ? data.next_page - 1 : page;
                    hasNext = data.has_next;
                }
            })
            .catch(error => {
                console.error('加载更多相册时出错:', error);
            })
            .finally(() => {
                isLoading = false;
                activeBtn.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
                initLoadMore();
            });
        }
         function handleScroll() {
            // 检查是否滚动到页面底部附近（100px以内）
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
                loadMoreAlbums();
            }
        }

        // 绑定事件
        // 绑定事件
        window.addEventListener('scroll', handleScroll);
        if (activeBtn) {
            activeBtn.addEventListener('click', loadMoreAlbums);
}
        
        // 初始化
        initLoadMore();
    }

    // 页面加载完成后初始化懒加载
    document.addEventListener('DOMContentLoaded', function() {
        initLazyLoading();
});