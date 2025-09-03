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
            
            // 防止重复提交
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn.disabled) return;
            submitBtn.disabled = true;
            
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
            const submitBtn = form.querySelector('button[type="submit"]');
            
            // 防止重复提交
            if (submitBtn.disabled) return;
            submitBtn.disabled = true;
            
            if (!content.trim()) {
                showMessage('回复内容不能为空！', 'danger');
                submitBtn.disabled = false;
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
    });
    
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

