document.addEventListener('DOMContentLoaded', function() {
    // 处理通知点击事件
    document.addEventListener('click', function(e) {
        const notificationItem = e.target.closest('.notification-item');
        if (notificationItem) {
            const notificationId = notificationItem.dataset.notificationId;
            if (notificationId) {
                fetch(`/photos/notification/${notificationId}/mark-as-read/`, {
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
            
            // 防止重复提交
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn.disabled) return;
            submitBtn.disabled = true;
            
            const formData = new FormData(this);
            const photoId = this.getAttribute('data-photo-id');
            
            fetch(`/photos/photo/${photoId}/comment/`, {
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
                    
                    // 局部刷新评论区（不再显示弹窗提示）
                    loadComments(photoId);
                } else {
                    showMessage(data.error || '评论添加失败！', 'danger');
                }
                // 重新启用提交按钮
                submitBtn.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('评论添加失败！', 'danger');
                submitBtn.disabled = false;
            });
        });
    }
    
    // 点赞功能
    const likeButtons = document.querySelectorAll('.like-btn');
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const photoId = this.getAttribute('data-photo-id');
            const icon = this.querySelector('i');
            const countElement = this.querySelector('.like-count');
            
            fetch(`/photos/photo/${photoId}/like/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新点赞状态和计数
                    if (data.is_liked) {
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-danger');
                    } else {
                        icon.classList.remove('fas', 'text-danger');
                        icon.classList.add('far');
                    }
                    countElement.textContent = data.like_count;
                } else {
                    // 处理错误（如未登录）
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        showMessage(data.error || '操作失败！', 'danger');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('操作失败！', 'danger');
            });
        });
    });
    
    // 收藏功能
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const photoId = this.getAttribute('data-photo-id');
            const icon = this.querySelector('i');
            const countElement = this.querySelector('.favorite-count');
            
            fetch(`/photos/photo/${photoId}/favorite/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新收藏状态和计数
                    if (data.is_favorited) {
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-warning');
                    } else {
                        icon.classList.remove('fas', 'text-warning');
                        icon.classList.add('far');
                    }
                    countElement.textContent = data.favorite_count;
                } else {
                    // 处理错误（如未登录）
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        showMessage(data.error || '操作失败！', 'danger');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('操作失败！', 'danger');
            });
        });
    });

    // 回复评论处理
    document.addEventListener('click', function(e) {
        const replyButton = e.target.closest('.reply-btn');
        if (replyButton) {
            const commentId = replyButton.getAttribute('data-comment-id');
            const content = prompt('请输入回复内容:');
            if (content) {
                // 防止重复提交
                const submitBtn = replyButton;
                if (submitBtn.disabled) return;
                submitBtn.disabled = true;
                
                fetch(`/photos/comment/${commentId}/reply/`, {
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
                        
                        // 局部刷新评论区（不再显示弹窗提示）
                        const photoId = document.getElementById('comment-form').getAttribute('data-photo-id');
                        loadComments(photoId);
                    } else {
                        showMessage(data.error || '回复添加失败！', 'danger');
                    }
                    // 重新启用提交按钮
                    submitBtn.disabled = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('回复添加失败！', 'danger');
                    submitBtn.disabled = false;
                });
            }
        }
    });
});

// 加载评论
function loadComments(photoId) {
    fetch(`/photos/photo/${photoId}/comments/`)
        .then(response => response.text())
        .then(html => {
            const commentsContainer = document.getElementById('comments-container');
            if (commentsContainer) {
                commentsContainer.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 显示消息
function showMessage(message, type) {
    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `alert alert-${type} alert-dismissible fade show`;
    messageElement.role = 'alert';
    messageElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到页面顶部
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(messageElement, container.firstChild);
    }
    
    // 3秒后自动消失
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.parentNode.removeChild(messageElement);
        }
    }, 3000);
}

// 获取Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}