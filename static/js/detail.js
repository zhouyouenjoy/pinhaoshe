document.addEventListener('DOMContentLoaded', function() {
    const photoId = document.querySelector('.photo-detail').dataset.photoId;
    const commentsList = document.querySelector('.comments-list');
    let isLoading = false;
    let currentOffset = 5; // 初始加载5条评论
    let hasMore = true; // 添加has_more标志
    let noMoreCommentsShown = false; // 标记是否已显示"没有更多评论"提示
    
    // 检查是否已滚动到页面底部
    function isBottomReached() {
        return window.innerHeight + window.scrollY >= document.body.offsetHeight - 500;
    }
    
    // 显示没有更多评论的提示
    function showNoMoreComments() {
        if (!noMoreCommentsShown) {
            const noMoreDiv = document.createElement('div');
            noMoreDiv.className = 'text-center text-muted py-3';
            noMoreDiv.textContent = '没有更多评论了';
            commentsList.parentNode.appendChild(noMoreDiv);
            noMoreCommentsShown = true;
        }
    }
    
    // 加载更多评论
    function loadMoreComments() {
        // 如果正在加载或没有更多评论，则返回
        if (isLoading || !hasMore) return;
        isLoading = true;

        fetch(`/load-more-comments/?photo_id=${photoId}&offset=${currentOffset}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.comments && data.comments.length > 0) {
                data.comments.forEach(comment => {
                    // 动态创建评论元素并添加到列表
                    const commentElement = document.createElement('div');
                    commentElement.innerHTML = comment.html;
                    commentsList.appendChild(commentElement);
                });
                currentOffset += data.comments.length;
                hasMore = data.has_more;
            } else {
                hasMore = false;
                showNoMoreComments();
            }
            isLoading = false;
        })
        .catch(error => {
            console.error('加载评论出错:', error);
            isLoading = false;
        });
    }

    // 初始加载后检查是否还有更多评论
    if (commentsList.children.length < 5) {
        hasMore = false;
        showNoMoreComments();
    }

    // 滚动事件监听
    window.addEventListener('scroll', function() {
        if (isBottomReached() && !isLoading && hasMore) {
            loadMoreComments();
        }
    });

    // 初始检查是否需要加载更多
    if (isBottomReached() && !isLoading && hasMore) {
        loadMoreComments();
    }
});