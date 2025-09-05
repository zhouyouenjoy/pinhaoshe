
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
            noMoreDiv.textContent = '已经到底了';
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
                    const pElement = tempDiv.querySelector('p');
                    if (pElement) {
                        console.log("评论<p>标签的值:", pElement.textContent);
                    } else {
                        console.log("未找到<p>标签，完整HTML:", comment.html);
                    }
                    
                    console.log("data.comments111:", data.comments);
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
            
            // 检查是否需要滚动到特定评论
            checkAndScrollToTargetComment();
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
    
    // 检查并滚动到目标评论
    function checkAndScrollToTargetComment() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#comment-')) {
            const targetElement = document.querySelector(hash);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // 添加高亮效果
                targetElement.style.transition = 'background-color 0.5s';
                targetElement.style.backgroundColor = '#fff3cd';
                setTimeout(() => {
                    targetElement.style.backgroundColor = '';
                }, 2000);
                return true;
            }
        }
        return false;
    }
    
    // 定期检查目标评论是否存在，如果不存在则继续加载更多评论
    function waitForTargetComment() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#comment-')) {
            // 首先检查目标评论是否已经存在
            if (checkAndScrollToTargetComment()) {
                return; // 如果找到了目标评论，直接返回
            }
            
            // 如果没有找到目标评论，继续加载更多评论
            let attempts = 0;
            const maxAttempts = 20; // 最多尝试20次
            
            const tryToFindComment = function() {
                attempts++;
                
                // 再次检查目标评论是否已经存在
                if (checkAndScrollToTargetComment()) {
                    return; // 如果找到了目标评论，直接返回
                }
                
                // 如果还没找到且还有更多评论可以加载，则加载更多评论
                if (hasMore && attempts < maxAttempts) {
                    loadMoreComments();
                    setTimeout(tryToFindComment, 1000); // 1秒后再次检查
                } else if (attempts >= maxAttempts) {
                    // 如果达到最大尝试次数仍未找到，直接跳转到锚点
                    if (hash) {
                        const targetElement = document.querySelector(hash);
                        if (targetElement) {
                            targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            // 添加高亮效果
                            targetElement.style.transition = 'background-color 0.5s';
                            targetElement.style.backgroundColor = '#fff3cd';
                            setTimeout(() => {
                                targetElement.style.backgroundColor = '';
                            }, 2000);
                        }
                    }
                }
            };
            
            // 开始尝试查找评论
            tryToFindComment();
        }
    }
    
    // 页面加载完成后，等待一段时间再检查目标评论
    setTimeout(waitForTargetComment, 1000);
});

document.addEventListener('DOMContentLoaded', function() {
    // 写评论按钮处理
    const writeCommentBtn = document.getElementById('write-comment-btn');
    const commentBtn = document.getElementById('comment-btn');
    const commentModal = document.getElementById('comment-modal');
    const commentModalOverlay = document.getElementById('comment-modal-overlay');
    const closeCommentModal = document.getElementById('close-comment-modal');
    const commentForm = document.getElementById('comment-form');
    const commentModalTitle = document.getElementById('comment-modal-title');
    const parentCommentIdInput = document.getElementById('parent-comment-id');
    const commentContent = document.getElementById('comment-content');
    const mentionSuggestions = document.getElementById('mention-suggestions');
    
    // 打开评论弹窗 - 用于发表新评论
    function openCommentModal() {
        // 重置表单状态为发表新评论
        commentModalTitle.textContent = '发表评论';
        parentCommentIdInput.value = '';
        commentContent.value = '';
        
        if (commentModal && commentModalOverlay) {
            commentModal.classList.add('show');
            commentModalOverlay.classList.add('show');
            document.body.style.overflow = 'hidden'; // 防止背景滚动
        }
    }
    
    // 打开回复弹窗 - 用于回复评论
    function openReplyModal(parentId) {
        // 设置表单状态为回复评论
        commentModalTitle.textContent = '回复评论';
        parentCommentIdInput.value = parentId;
        commentContent.value = '';
        commentContent.focus();
        
        if (commentModal && commentModalOverlay) {
            commentModal.classList.add('show');
            commentModalOverlay.classList.add('show');
            document.body.style.overflow = 'hidden'; // 防止背景滚动
        }
    }
    
    // 关闭评论弹窗
    function closeCommentModalFunc() {
        if (commentModal && commentModalOverlay) {
            commentModal.classList.remove('show');
            commentModalOverlay.classList.remove('show');
            document.body.style.overflow = ''; // 恢复背景滚动
        }
        // 隐藏@用户提示列表
        hideMentionSuggestions();
    }
    
    // 绑定写评论按钮事件（底部导航栏）
    if (writeCommentBtn) {
        writeCommentBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openCommentModal();
        });
    }
    
    // 绑定评论按钮事件（底部导航栏）- 滚动到评论区
    if (commentBtn) {
        commentBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const commentsSection = document.getElementById('comments');
            if (commentsSection) {
                commentsSection.scrollIntoView({behavior: 'smooth'});
            }
        });
    }
    
    // 绑定关闭按钮事件
    if (closeCommentModal) {
        closeCommentModal.addEventListener('click', closeCommentModalFunc);
    }
    
    // 绑定遮罩层点击事件
    if (commentModalOverlay) {
        commentModalOverlay.addEventListener('click', closeCommentModalFunc);
    }
    
    // 绑定评论表单提交事件
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 防止重复提交
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton.disabled) return;
            submitButton.disabled = true;
            
            const formData = new FormData(this);
            const content = formData.get('content');
            const parentId = formData.get('parent_id');
            const photoId = document.querySelector('.photo-detail').getAttribute('data-photo-id');
            
            if (!content.trim()) {
                alert('评论内容不能为空');
                submitButton.disabled = false;
                return;
            }
            
            // 根据是否有parent_id确定是新评论还是回复
            let url = `/photo/${photoId}/comment/`;
            if (parentId) {
                url = `/comment/${parentId}/reply/`;
            }
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    submitButton.disabled = false;
                    return;
                }
                
                // 关闭模态框
                closeCommentModalFunc();
                
                // 清空表单
                document.getElementById('comment-content').value = '';
                document.getElementById('parent-comment-id').value = '';
                
                // 局部刷新评论区（不再显示弹窗提示）
                refreshCommentsAndScrollToLatest(data.comment_id);
                
                // 重新启用提交按钮
                submitButton.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('提交失败，请重试');
                submitButton.disabled = false;
            });
        });
    }
    
    // @用户功能相关函数
    let mentionSearchTerm = '';
    let mentionStartPos = -1;
    let filteredUsers = [];
    let selectedUserIndex = -1;
    
    // 隐藏@用户提示列表
    function hideMentionSuggestions() {
        mentionSuggestions.style.display = 'none';
        mentionSearchTerm = '';
        mentionStartPos = -1;
        filteredUsers = [];
        selectedUserIndex = -1;
    }
    
    // 显示@用户提示列表
    function showMentionSuggestions(users) {
        if (users.length === 0) {
            hideMentionSuggestions();
            return;
        }
        
        // 清空现有内容
        mentionSuggestions.innerHTML = '';
        
        // 添加用户列表
        users.forEach((user, index) => {
            const userItem = document.createElement('a');
            userItem.href = '#';
            userItem.className = 'dropdown-item d-flex align-items-center';
            userItem.innerHTML = `
                ${user.avatar ? 
                    `<img src="${user.avatar}" alt="${user.username}" class="rounded-circle me-2" style="width: 30px; height: 30px; object-fit: cover;">` :
                    `<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center me-2" style="width: 30px; height: 30px;">
                        <span class="text-white" style="font-size: 0.7rem;">${user.username.charAt(0).toUpperCase()}</span>
                    </div>`
                }
                <span>${user.username}</span>
            `;
            
            // 高亮选中项
            if (index === selectedUserIndex) {
                userItem.classList.add('active');
            }
            
            // 点击选择用户
            userItem.addEventListener('click', function(e) {
                e.preventDefault();
                selectMentionUser(user.username);
            });
            
            mentionSuggestions.appendChild(userItem);
        });
        
        // 显示列表
        mentionSuggestions.style.display = 'block';
    }
    
    // 选择@的用户
    function selectMentionUser(username) {
        if (mentionStartPos === -1) return;
        
        // 替换@后的文本为完整的用户名
        const currentContent = commentContent.value;
        const beforeMention = currentContent.substring(0, mentionStartPos);
        const afterMention = currentContent.substring(mentionStartPos + mentionSearchTerm.length + 1); // +1 for @
        commentContent.value = beforeMention + '@' + username + ' ' + afterMention;
        
        // 调整光标位置到插入用户名之后
        const newCursorPos = mentionStartPos + username.length + 2; // +2 for @ and space
        commentContent.setSelectionRange(newCursorPos, newCursorPos);
        
        // 隐藏提示列表
        hideMentionSuggestions();
        
        // 重新聚焦到输入框
        commentContent.focus();
    }
    
    // 监听评论输入框的输入事件
    if (commentContent) {
        commentContent.addEventListener('input', function(e) {
            const cursorPos = this.selectionStart;
            const content = this.value;
            
            // 查找光标前最近的@符号
            let atPos = -1;
            for (let i = cursorPos - 1; i >= 0; i--) {
                if (content[i] === '@') {
                    // 检查@前一个字符是否是空格或在开头
                    if (i === 0 || /\s/.test(content[i - 1])) {
                        atPos = i;
                        break;
                    }
                } else if (/\s/.test(content[i])) {
                    // 遇到空格就停止查找
                    break;
                }
            }
            
            // 如果找到了@符号
            if (atPos !== -1) {
                mentionStartPos = atPos;
                mentionSearchTerm = content.substring(atPos + 1, cursorPos);
                
                // 如果搜索词不为空，获取匹配的用户
                if (mentionSearchTerm.length > 0) {
                    fetch(`/search-users/?q=${encodeURIComponent(mentionSearchTerm)}`, {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        filteredUsers = data.users || [];
                        selectedUserIndex = -1;
                        showMentionSuggestions(filteredUsers);
                    })
                    .catch(error => {
                        console.error('Error fetching users:', error);
                        hideMentionSuggestions();
                    });
                } else {
                    hideMentionSuggestions();
                }
            } else {
                hideMentionSuggestions();
            }
        });
        
        // 监听键盘事件处理导航和选择
        commentContent.addEventListener('keydown', function(e) {
            if (mentionSuggestions.style.display === 'block') {
                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        selectedUserIndex = (selectedUserIndex + 1) % filteredUsers.length;
                        showMentionSuggestions(filteredUsers);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        selectedUserIndex = (selectedUserIndex - 1 + filteredUsers.length) % filteredUsers.length;
                        showMentionSuggestions(filteredUsers);
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (selectedUserIndex >= 0 && selectedUserIndex < filteredUsers.length) {
                            selectMentionUser(filteredUsers[selectedUserIndex].username);
                        }
                        break;
                    case 'Escape':
                        e.preventDefault();
                        hideMentionSuggestions();
                        break;
                }
            }
        });
        
        // 点击其他地方隐藏@用户提示列表
        document.addEventListener('click', function(e) {
            if (!commentContent.contains(e.target) && !mentionSuggestions.contains(e.target)) {
                hideMentionSuggestions();
            }
        });
    }
    
    // 使用事件委托处理评论区的各种交互事件
    const commentsContainer = document.getElementById('comments');
    if (commentsContainer) {
        commentsContainer.addEventListener('click', function(e) {
            // 处理回复按钮点击事件
            const replyBtn = e.target.closest('.reply-btn');
            if (replyBtn) {
                e.preventDefault();
                e.stopPropagation();
                const commentId = replyBtn.getAttribute('data-comment-id');
                openReplyModal(commentId);
                return;
            }
            
            // 处理取消回复按钮点击事件
            const cancelReplyBtn = e.target.closest('.cancel-reply');
            if (cancelReplyBtn) {
                e.preventDefault();
                e.stopPropagation();
                const form = cancelReplyBtn.closest('.reply-form');
                if (form) {
                    form.style.display = 'none';
                    const textarea = form.querySelector('textarea');
                    if (textarea) {
                        textarea.value = '';
                    }
                }
                return;
            }
            
            // 处理删除评论按钮点击事件
            const deleteCommentBtn = e.target.closest('.delete-comment-btn');
            if (deleteCommentBtn) {
                e.preventDefault();
                e.stopPropagation();
                const commentId = deleteCommentBtn.getAttribute('data-comment-id');
                
                if (confirm('确定要删除这条评论吗？')) {
                    fetch(`/comment/${commentId}/delete/`, {
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
                        
                        // 显示成功消息
                        alert('评论删除成功');
                        
                        // 局部刷新整个评论区
                        refreshComments();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('评论删除失败，请重试');
                    });
                }
                return;
            }
            
            // 处理评论点赞按钮点击事件
            const commentLikeBtn = e.target.closest('.comment-action-btn');
            if (commentLikeBtn && !commentLikeBtn.classList.contains('reply-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const commentId = commentLikeBtn.getAttribute('data-comment-id');
                
                fetch(`/comment/${commentId}/like/`, {
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
                    
                    // 更新点赞按钮样式和计数
                    const likeCountElement = commentLikeBtn.querySelector('.like-count');
                    if (data.liked) {
                        commentLikeBtn.classList.add('liked');
                    } else {
                        commentLikeBtn.classList.remove('liked');
                    }
                    likeCountElement.textContent = data.like_count;
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('点赞失败，请重试');
                });
                return;
            }
        });
        
        // 处理回复表单提交事件
        commentsContainer.addEventListener('submit', function(e) {
            const replyForm = e.target.closest('.reply-form-inner');
            if (replyForm) {
                e.preventDefault();
                e.stopPropagation();
                
                const commentId = replyForm.getAttribute('data-comment-id');
                const textarea = replyForm.querySelector('textarea');
                const content = textarea.value.trim();
                
                if (!content) {
                    alert('回复内容不能为空');
                    return;
                }
                
                // 发送回复请求
                fetch(`/comment/${commentId}/reply/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({content: content})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    
                    // 隐藏表单并清空内容
                    const replyFormContainer = document.getElementById(`reply-form-${commentId}`);
                    if (replyFormContainer) {
                        replyFormContainer.style.display = 'none';
                        textarea.value = '';
                    }
                    
                    // 显示成功消息
                    alert('回复成功');
                    
                    // 局部刷新整个评论区并滚动到最新回复
                    refreshCommentsAndScrollToLatest(data.comment_id);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('回复失败，请重试');
                });
            }
        });
    }
    
    function refreshComments(newCommentId = null) {
        const photoId = document.querySelector('.photo-detail').getAttribute('data-photo-id');
        fetch(`/photo/${photoId}/comments/`)
        .then(response => response.text())
        .then(html => {
            const commentsContainer = document.querySelector('#comments .comments-list');
            if (commentsContainer) {
                commentsContainer.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error refreshing comments:', error);
            alert('刷新评论失败，请手动刷新页面');
        });
    }

    // 局部刷新评论区并滚动到最新评论
    function refreshCommentsAndScrollToLatest(newCommentId = null) {
        const photoId = document.querySelector('.photo-detail').getAttribute('data-photo-id');
        fetch(`/photo/${photoId}/comments/`)
        .then(response => response.text())
        .then(html => {
            const commentsContainer = document.querySelector('#comments .comments-list');
            if (commentsContainer) {
                commentsContainer.innerHTML = html;
            }
            
            // 滚动到指定评论并高亮
            setTimeout(() => {
                let targetElement = null;
                if (newCommentId) {
                    targetElement = document.querySelector(`#comment-${newCommentId}`);
                } else {
                    targetElement = document.querySelector('.comment-item');
                }
                
                if (targetElement) {
                    targetElement.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center'
                    });
                    
                    targetElement.style.transition = 'background-color 0.5s';
                    targetElement.style.backgroundColor = '#fff3cd';
                    setTimeout(() => {
                        targetElement.style.backgroundColor = '';
                    }, 2000);
                }
            }, 100);
        })
        .catch(error => {
            console.error('Error refreshing comments:', error);
            alert('刷新评论失败，请手动刷新页面');
        });
    }

});


