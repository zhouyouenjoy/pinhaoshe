
window.addEventListener('DOMContentLoaded', function() {
    // 处理关注按钮点击事件
    const followBtn = document.getElementById('follow-btn');
    if (followBtn) {
        followBtn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const button = this;
            
            fetch(`/toggle-follow/${userId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                // 更新按钮文本和样式
                const followText = document.getElementById('follow-text');
                if (data.is_following) {
                    followText.textContent = '取消关注';
                    button.classList.remove('btn-outline-primary');
                    button.classList.add('btn-primary');
                } else {
                    followText.textContent = '关注';
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-outline-primary');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('操作失败，请重试');
            });
        });
    }
    const photoId = document.querySelector('.photo-detail').dataset.photoId;
    const commentsList = document.querySelector('.comments-list');
    let isLoading = false;
    let currentOffset = 0; // 初始加载5条评论
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
            noMoreDiv.textContent = '没有更多评论了2';
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
                    
                    // 提取并输出<p>标签的值到控制台
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = comment.html;
                    const pElement = tempDiv.querySelector('div.comment-text');
                    if (pElement) {
                        console.log("评论值:", pElement.textContent);
                    } else {
                        // 标准化输出HTML
                        const tempContainer = document.createElement('div');
                        tempContainer.innerHTML = comment.html;
                        const standardizedHTML = tempContainer.innerHTML;
                        console.log("标准化HTML:", standardizedHTML);
                    }
                    
                });
                currentOffset += data.comments.length;
            }
            
            // 更新hasMore标志
            hasMore = data.has_more;
            
            // 如果没有更多评论，显示提示
            if (!hasMore) {
                showNoMoreComments();
            }
            
            isLoading = false;
        })
        .catch(error => {
            console.error('Error:', error);
            isLoading = false;
        });
    }
    
    // 监听滚动事件
    window.addEventListener('scroll', function() {
        if (isBottomReached() && !noMoreCommentsShown) {
            loadMoreComments();
        }
    });
    
    // 评论点赞处理
    document.addEventListener('click', function(e) {
        // 处理评论点赞按钮点击
        if (e.target.closest('.comment-action-btn') && !e.target.closest('.reply-btn')) {
            e.preventDefault();
            e.stopPropagation();
            
            const likeBtn = e.target.closest('.comment-action-btn');
            const commentId = likeBtn.getAttribute('data-comment-id');
            
            fetch(`/comment/${commentId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.liked !== undefined) {
                    // 更新点赞按钮样式
                    if (data.liked) {
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('liked');
                    }
                    
                    // 更新点赞数
                    const likeCount = likeBtn.querySelector('.like-count');
                    if (likeCount) {
                        likeCount.textContent = data.like_count;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('点赞操作失败！');
            });
        }
    });
});


