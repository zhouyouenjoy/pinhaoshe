// 操作按钮处理
document.addEventListener('DOMContentLoaded', function() {
    // 点击操作按钮显示/隐藏菜单
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.message-actions-btn');
        if (btn) {
            e.stopPropagation();
            const menu = btn.nextElementSibling;
            const isShowing = menu.classList.contains('show');
            
            // 隐藏所有其他菜单
            document.querySelectorAll('.message-actions-menu.show').forEach(m => {
                if (m !== menu) m.classList.remove('show');
            });
            
            // 切换当前菜单
            menu.classList.toggle('show', !isShowing);
        } else {
            // 点击其他地方隐藏所有菜单
            document.querySelectorAll('.message-actions-menu.show').forEach(m => {
                m.classList.remove('show');
            });
        }
    });
    
    // 为通知项目添加点击事件监听器
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', function(e) {
            // 检查点击的是否是操作按钮或其子元素
            if (e.target.closest('.message-actions-btn') || e.target.closest('.message-actions-menu')) {
                return; // 如果是操作按钮，则不执行跳转
            }
            
            const notificationId = this.dataset.notificationId;
            const notificationLink = this.querySelector('.notification-link');
            
            if (notificationLink) {
                // 标记通知为已读
                markNotificationAsRead(e, notificationId);
                // 跳转到链接
                window.location.href = notificationLink.href;
            }
        });
    });
    
    // 处理通知链接点击事件
    function handleNotificationClick(event, notificationType, photoId, commentId, targetUrl) {
        // 防止事件冒泡
        event.stopPropagation();
        event.preventDefault();
        
        // 获取通知项
        const notificationItem = event.currentTarget.closest('.notification-item');
        const notificationId = notificationItem.dataset.notificationId;
        
        // 标记通知为已读
        markNotificationAsRead(event, notificationId);
        
        // 对于评论相关的通知，处理懒加载评论的情况
        if (['mention', 'comment', 'reply', 'comment_like'].includes(notificationType)) {
            // 直接跳转到照片详情页，让详情页处理评论的懒加载和定位
            window.location.href = targetUrl;
            return;
        }
        
        // 对于非评论类通知，直接跳转
        window.location.href = targetUrl;
    }
    
    // 为所有通知项添加点击事件监听器
    document.addEventListener('DOMContentLoaded', function() {
        // 为通知项添加点击事件监听器
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', function(e) {
                // 检查点击的是否是操作按钮或其子元素
                if (e.target.closest('.message-actions-btn') || e.target.closest('.message-actions-menu')) {
                    return; // 如果是操作按钮，则不执行跳转
                }
                
                const notificationLink = this.querySelector('.notification-link');
                if (notificationLink) {
                    // 调用链接的点击事件
                    notificationLink.click();
                }
            });
        });
    });
});

// 标记私信为已读并跳转
function markMessageAsReadAndRedirect(event, messageId, redirectUrl) {
    event.stopPropagation();
    
    // 先发送标记为已读的请求
    fetch(`/message/${messageId}/mark-as-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    }).then(response => {
        if (response.ok) {
            // 更新未读计数
            const unreadBadge = document.querySelector('#private-messages-tab .badge');
            if (unreadBadge) {
                const currentCount = parseInt(unreadBadge.textContent);
                if (currentCount > 0) {
                    unreadBadge.textContent = currentCount - 1;
                }
                // 如果计数为0，移除徽章
                if (currentCount - 1 === 0) {
                    unreadBadge.remove();
                }
            }
            
            // 移除消息项的未读样式
            const messageItem = event.currentTarget;
            messageItem.classList.remove('unread');
            const unreadDot = messageItem.querySelector('.unread-dot');
            if (unreadDot) {
                unreadDot.remove();
            }
        }
    }).catch(error => {
        console.error('标记消息为已读失败:', error);
    }).finally(() => {
        // 无论成功与否都跳转到聊天页面
        window.location = redirectUrl;
    });
}

// 标记对话为已读
function markMessageAsRead(event, messageId, fromAction = false) {
    if (fromAction) {
        event.stopPropagation();
        event.preventDefault();
    } else {
        return; // 点击消息内容不自动标记为已读
    }
    
    fetch(`/message/${messageId}/mark-as-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    }).then(response => {
        if (response.ok) {
            // 局部刷新消息列表
            fetch(window.location.pathname + '?partial=messages', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.getElementById('private-messages');
                if (newContent) {
                    document.getElementById('private-messages').innerHTML = newContent.innerHTML;
                }
            })
            .catch(error => {
                console.error('刷新消息列表失败:', error);
                location.reload(); // 回退到整页刷新
            });
        }
    });
}

// 标记通知为已读
function markNotificationAsRead(event, notificationId) {
    event.stopPropagation();
    
    // 构造正确的URL路径
    const url = `/photos/notification/${notificationId}/mark-as-read/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    }).then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Network response was not ok.');
    }).then(data => {
        if (data.success) {
            // 更新未读计数
            const tabs = ['like-favorite', 'comment-mention', 'follow-notifications'];
            tabs.forEach(tabId => {
                const badge = document.querySelector(`#${tabId}-tab .badge`);
                if (badge) {
                    const currentCount = parseInt(badge.textContent);
                    if (currentCount > 0) {
                        badge.textContent = currentCount - 1;
                    }
                    // 如果计数为0，移除徽章
                    if (currentCount - 1 === 0) {
                        badge.remove();
                    }
                }
            });
            
            // 移除通知项的未读样式
            const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.classList.remove('unread');
                const unreadDot = notificationItem.querySelector('.unread-dot');
                if (unreadDot) {
                    unreadDot.remove();
                }
            }
        }
    }).catch(error => {
        console.error('标记通知为已读失败:', error);
    });
}

// 跳转到评论锚点的函数
function scrollToCommentAnchor(anchor) {
    // 如果锚点存在，直接跳转
    const element = document.querySelector(anchor);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // 添加高亮效果
        element.style.transition = 'background-color 0.5s';
        element.style.backgroundColor = '#fff3cd';
        setTimeout(() => {
            element.style.backgroundColor = '';
        }, 2000);
        return true;
    }
    return false;
}

// 等待评论加载并跳转到锚点
function waitForCommentAndScroll(photoId, anchor, maxAttempts = 20) {
    let attempts = 0;
    
    const checkAndScroll = function() {
        attempts++;
        if (scrollToCommentAnchor(anchor)) {
            return; // 成功找到并跳转到锚点
        }
        
        // 如果超过最大尝试次数，就停止
        if (attempts >= maxAttempts) {
            // 尝试直接跳转到锚点
            window.location.hash = anchor;
            return;
        }
        
        // 继续等待并检查
        setTimeout(checkAndScroll, 500);
    };
    
    // 开始检查
    checkAndScroll();
}

// 加载评论并跳转到指定评论
function loadCommentsAndScroll(photoId, commentId, targetUrl) {
    // 先跳转到照片详情页
    window.location.href = targetUrl;
    
    // 在新页面加载后，等待评论加载完成再跳转到指定评论
    // 这个逻辑将在照片详情页中处理
}

// 处理通知链接点击事件
function handleNotificationClick(event, notificationType, photoId, commentId, targetUrl) {
    event.preventDefault();
    const notificationItem = event.currentTarget.closest('.notification-item');
    const notificationId = notificationItem.dataset.notificationId;
    
    // 标记通知为已读
    markNotificationAsRead(event, notificationId);
    
    // 对于评论相关的通知，处理懒加载评论的情况
    if (['mention', 'comment', 'reply', 'comment_like'].includes(notificationType)) {
        // 直接跳转到照片详情页，让详情页处理评论的懒加载和定位
        window.location.href = targetUrl;
        return;
    }
    
    // 对于非评论类通知，直接跳转
    window.location.href = targetUrl;
}

// 删除对话
function deleteConversation(event, userId, button) {
    event.stopPropagation();
    event.preventDefault();
    
    if (confirm('确定要删除这个对话吗？')) {
        // 添加加载状态
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        // 确保获取CSRF token
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
                         document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        
        if (!csrfToken) {
            alert('无法获取安全令牌，请刷新页面后重试');
            button.innerHTML = '<i class="fas fa-trash"></i>';
            button.disabled = false;
            return;
        }
        
        fetch(`/delete-conversation/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 局部刷新消息列表
                fetch(window.location.pathname + '?partial=messages', {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newContent = doc.getElementById('private-messages');
                    if (newContent) {
                        document.getElementById('private-messages').innerHTML = newContent.innerHTML;
                    }
                })
                .catch(error => {
                    console.error('刷新消息列表失败:', error);
                    location.reload(); // 回退到整页刷新
                });
            } else {
                alert('删除失败: ' + (data.error || '未知错误'));
                button.innerHTML = '<i class="fas fa-trash"></i>';
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('删除对话失败:', error);
            alert('删除对话失败，请重试');
            button.innerHTML = '<i class="fas fa-trash"></i>';
            button.disabled = false;
        });
    }
}

// 置顶对话
function pinConversation(event, userId) {
    event.stopPropagation();
    event.preventDefault();
    
    fetch(`/pin-conversation/${userId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    }).then(response => {
        if (response.ok) {
            // 局部刷新消息列表
            fetch(window.location.pathname + '?partial=messages', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.getElementById('private-messages');
                if (newContent) {
                    document.getElementById('private-messages').innerHTML = newContent.innerHTML;
                }
            })
            .catch(error => {
                console.error('刷新消息列表失败:', error);
                location.reload(); // 回退到整页刷新
            });
        }
    }).catch(error => {
        console.error('置顶对话失败:', error);
        alert('操作失败，请重试');
    });
}

// 全局变量
let currentTab = 'private-messages'; // 当前标签页，默认为私信
let currentPage = 1; // 当前页码
let hasMoreData = true; // 是否还有更多数据
let loading = false; // 是否正在加载
let isLoadingNew = false; // 是否正在加载新数据

// 加载更多历史消息（下滑触底加载）
function loadMoreMessages() {
    if (loading || !hasMoreData) return;
    
    loading = true;
    
    // 显示加载指示器
    const loader = document.createElement('div');
    loader.className = 'text-center py-3';
    loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
    document.querySelector(`#${currentTab}`).appendChild(loader);
    
    // 构造请求URL
    let url = window.location.pathname + `?partial=${currentTab}`;
    currentPage++;
    
    // 根据当前标签页添加对应的页码参数
    switch(currentTab) {
        case 'private-messages':
            url += `&message_page=${currentPage}`;
            break;
        case 'like-favorite':
            url += `&like_favorite_page=${currentPage}`;
            break;
        case 'comment-mention':
            url += `&comment_mention_page=${currentPage}`;
            break;
        case 'follow-notifications':
            url += `&follow_page=${currentPage}`;
            break;
    }
    
    // 发送AJAX请求
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        // 解析返回的HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 获取对应标签页的内容
        const newContent = doc.getElementById(currentTab);
        if (newContent) {
            // 查找新内容中的消息项
            const items = newContent.querySelectorAll('.message-item, .notification-item');
            
            if (items.length > 0) {
                // 将新项目添加到容器末尾
                const container = document.querySelector(`#${currentTab} .messages-container-content`);
                items.forEach(item => {
                    // 检查是否已存在相同ID的项目
                    const itemId = item.dataset.notificationId || item.dataset.messageId;
                    if (itemId) {
                        const existingItem = container.querySelector(`[data-notification-id="${itemId}"], [data-message-id="${itemId}"]`);
                        if (!existingItem) {
                            container.appendChild(item);
                        }
                    } else {
                        container.appendChild(item);
                    }
                });
            } else {
                // 没有更多数据
                hasMoreData = false;
            }
        }
    })
    .catch(error => {
        console.error('加载更多数据失败:', error);
        // 显示错误信息
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-center py-3 text-danger';
        errorDiv.textContent = '加载失败，请重试';
        document.querySelector(`#${currentTab}`).appendChild(errorDiv);
        // 出错时恢复currentPage，以便用户可以重试
        currentPage--;
    })
    .finally(() => {
        // 移除加载指示器
        const loader = document.querySelector(`#${currentTab} .text-center.py-3`);
        if (loader) {
            loader.remove();
        }
        loading = false;
    });
}

// 监听标签页切换事件
document.addEventListener('DOMContentLoaded', function() {
    // 监听标签页显示事件
    const tabElements = document.querySelectorAll('#mainTabs button[data-bs-toggle="tab"]');
    tabElements.forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', function (event) {
            // 更新当前标签页
            currentTab = event.target.getAttribute('data-bs-target').substring(1);
            // 重置分页相关变量
            currentPage = 1;
            hasMoreData = true;
            loading = false;
            isLoadingNew = false;
        });
    });
    
    // 监听滚动事件以实现无限滚动
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => {
        const messagesContainer = pane.querySelector('.messages-container-content');
        if (messagesContainer) {
            // 防止触摸事件穿透
            messagesContainer.addEventListener('touchstart', function(e) {
                this.scrollTopStart = this.scrollTop;
            });
            
            messagesContainer.addEventListener('touchmove', function(e) {
                const scrollTop = this.scrollTop;
                const scrollHeight = this.scrollHeight;
                const offsetHeight = this.offsetHeight;
                const scrollTopEnd = scrollTopStart + e.touches[0].clientY - e.touches[0].clientY;
                
                // 判断是否在顶部或底部
                if ((scrollTop === 0 && e.touches[0].clientY > e.touches[0].clientY) || 
                    (scrollTop + offsetHeight >= scrollHeight && e.touches[0].clientY < e.touches[0].clientY)) {
                    e.preventDefault();
                }
            });
            
            messagesContainer.addEventListener('scroll', function() {
                const container = messagesContainer;
                // 检查是否滚动到顶部（加载最新消息）
                if (container.scrollTop <= 10) {
                    loadNewMessages();
                }
                // 检查是否滚动到底部（加载历史消息）
                else if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {
                    loadMoreMessages();
                }
            });
        }
    });
});
