document.addEventListener('DOMContentLoaded', function() {
    // 处理通知点击事件
    document.addEventListener('click', function(e) {
        const notificationItem = e.target.closest('.notification-item');
        if (notificationItem) {
            const notificationId = notificationItem.dataset.notificationId;
            if (notificationId) {
                fetch(`/notification/${notificationId}/mark-as-read/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 更新UI
                        notificationItem.classList.remove('unread');
                        const markAsReadBtn = notificationItem.querySelector('.mark-as-read');
                        if (markAsReadBtn) markAsReadBtn.remove();
                        
                        // 更新未读计数
                        const unreadBadge = document.querySelector('#notifications-tab .badge');
                        if (unreadBadge && data.unread_count !== undefined) {
                            unreadBadge.textContent = data.unread_count;
                        }
                    } else {
                        console.error('标记通知为已读失败:', data.error);
                    }
                })
                .catch(error => {
                    console.error('标记通知为已读时出错:', error);
                });
            }
        }
    });

    // 评论提交处理
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const photoId = this.getAttribute('data-photo-id');
            
            fetch(`/photo/${photoId}/comment/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 清空评论输入框
                    document.querySelector('#comment-form textarea').value = '';
                    
                    // 局部刷新评论区
                    loadComments(photoId);
                    
                    // 显示成功消息
                    showMessage('评论添加成功！', 'success');
                } else {
                    showMessage(data.error || '评论添加失败！', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('评论添加失败！', 'danger');
            });
        });
    }
    
    // 回复按钮点击处理
    document.addEventListener('click', function(e) {
        // 修复：使用closest方法查找.reply-btn元素，而不仅仅是检查e.target
        if (e.target.closest('.reply-btn')) {
            const replyBtn = e.target.closest('.reply-btn');
            const commentId = replyBtn.getAttribute('data-comment-id');
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            if (replyForm) {
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            }
        }
        
        // 取消回复按钮处理
        if (e.target.classList.contains('cancel-reply')) {
            const replyForm = e.target.closest('.reply-form');
            if (replyForm) {
                replyForm.style.display = 'none';
            }
        }
        
        // 提交回复处理（表单提交）
        if (e.target.classList.contains('reply-form-inner')) {
            e.preventDefault();
            const form = e.target;
            const commentId = form.getAttribute('data-comment-id');
            const content = form.querySelector('textarea').value;
            
            if (!content.trim()) {
                showMessage('回复内容不能为空！', 'danger');
                return;
            }
            
            fetch(`/comment/${commentId}/reply/`, {
                method: 'POST',
                body: JSON.stringify({content: content}),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 隐藏回复表单
                    const replyForm = document.getElementById(`reply-form-${commentId}`);
                    if (replyForm) {
                        replyForm.style.display = 'none';
                        replyForm.querySelector('textarea').value = '';
                    }
                    
                    // 局部刷新评论区
                    const photoId = document.getElementById('comment-form').getAttribute('data-photo-id');
                    loadComments(photoId);
                    
                    // 显示成功消息
                    showMessage('回复添加成功！', 'success');
                } else {
                    showMessage(data.error || '回复添加失败！', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('回复添加失败！', 'danger');
            });
        }
        
        // 评论点赞处理
        if (e.target.closest('.comment-like-btn')) {
            const likeBtn = e.target.closest('.comment-like-btn');
            const commentId = likeBtn.getAttribute('data-comment-id');
            
            fetch(`/comment/${commentId}/like/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.liked !== undefined) {
                    // 更新点赞按钮样式
                    if (data.liked) {
                        likeBtn.classList.remove('text-secondary');
                        likeBtn.classList.add('text-danger');
                        likeBtn.classList.add('liked');
                    } else {
                        likeBtn.classList.remove('text-danger');
                        likeBtn.classList.remove('liked');
                        likeBtn.classList.add('text-secondary');
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
                showMessage('点赞操作失败！', 'danger');
            });
        }
    });
    
    // 加载评论区
    function loadComments(photoId) {
        fetch(`/photo/${photoId}/comments/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.text())
        .then(html => {
            const commentsContainer = document.getElementById('comments-container');
            if (commentsContainer) {
                commentsContainer.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('评论加载失败！', 'danger');
        });
    }
    
    // 显示消息
    function showMessage(message, type) {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `alert alert-${type} alert-dismissible fade show`;
        messageEl.role = 'alert';
        messageEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // 插入到页面顶部
        const container = document.querySelector('.main-content') || document.body;
        container.insertBefore(messageEl, container.firstChild);
        
        // 3秒后自动移除消息
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 3000);
    }
    
    // 辅助函数：从cookie获取CSRF令牌
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});

// 递归渲染评论树的函数
function renderCommentTree(comment, depth = 0) {
    const indent = depth * 20; // 每层缩进20px
    
    let html = `
    <div class="comment-item" id="comment-${comment.id}" style="margin-left: ${indent}px;">
        <div class="comment-header">
            <div class="d-flex align-items-center">
    `;
    
    if (comment.avatar_url) {
        html += `<img src="${comment.avatar_url}" alt="${comment.username}" class="comment-avatar">`;
    } else {
        html += `
                <div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                    <span class="text-white" style="font-size: 0.8rem;">${comment.username.charAt(0).toUpperCase()}</span>
                </div>
        `;
    }
    
    html += `
                <div>
                    <a href="/my_info/?user_id=${comment.user_id}" class="comment-author">
                        ${comment.username}
                    </a>
                    <div class="text-muted" style="font-size: 0.8rem;">
                        ${comment.created_at}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="comment-content">
            ${comment.content}
        </div>
        
        <div class="comment-footer">
            <div class="comment-actions">
    `;
    
    if (comment.user_authenticated) {
        html += `
                <button class="comment-action-btn ${comment.liked ? 'liked text-danger' : 'text-secondary'}" 
                        data-comment-id="${comment.id}">
                    <i class="fas fa-thumbs-up"></i>
                    <span class="like-count">${comment.like_count}</span>
                </button>
                <button class="comment-action-btn reply-btn" data-comment-id="${comment.id}">
                    <i class="fas fa-reply"></i> 回复
                </button>
        `;
    } else {
        html += `
                <a href="/login/" class="comment-action-btn">
                    <i class="fas fa-thumbs-up"></i>
                    <span class="like-count">${comment.like_count}</span>
                </a>
                <a href="/login/" class="comment-action-btn">
                    <i class="fas fa-reply"></i> 回复
                </a>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    // 回复表单
    if (comment.user_authenticated) {
        html += `
        <div class="reply-form" id="reply-form-${comment.id}" style="display: none;">
            <form class="reply-form-inner" data-comment-id="${comment.id}">
                <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken')}">
                <div class="mb-2">
                    <textarea class="form-control form-control-sm" name="content" rows="2" placeholder="写下你的回复..." required></textarea>
                </div>
                <div class="text-end">
                    <button type="button" class="btn btn-sm btn-secondary cancel-reply">取消</button>
                    <button type="submit" class="btn btn-sm btn-primary">提交回复</button>
                </div>
            </form>
        </div>
        `;
    }
    
    // 递归渲染子评论
    if (comment.replies && comment.replies.length > 0) {
        html += '<div class="replies-container">';
        comment.replies.forEach(reply => {
            html += renderCommentTree(reply, depth + 1);
        });
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}