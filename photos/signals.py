from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Photo, Comment, Like, Favorite, Notification, CommentLike


@receiver(post_save, sender=Photo)
def photo_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Photo post_save
    """
    if created:
        # Handle newly created photo
        pass


@receiver(post_delete, sender=Photo)
def photo_post_delete(sender, instance, **kwargs):
    """
    Signal handler for Photo post_delete
    """
    # Handle photo deletion
    pass


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """
    当用户收到评论时发送通知
    """
    if created:
        # 检查是否是回复评论
        if instance.parent:
            # 回复评论 - 通知被回复的评论作者
            parent_comment_owner = instance.parent.user
            if parent_comment_owner != instance.user:
                Notification.objects.create(
                    recipient=parent_comment_owner,
                    sender=instance.user,
                    notification_type='reply',
                    content=f'{instance.user.username} 回复了你的评论: {instance.content[:50]}{"..." if len(instance.content) > 50 else ""}',
                    related_object_id=instance.id
                )
        else:
            # 发表评论 - 通知照片所有者
            photo_owner = instance.photo.uploaded_by
            if photo_owner != instance.user:
                Notification.objects.create(
                    recipient=photo_owner,
                    sender=instance.user,
                    notification_type='comment',
                    content=f'{instance.user.username} 评论了你的照片: {instance.content[:50]}{"..." if len(instance.content) > 50 else ""}',
                    related_object_id=instance.id
                )


@receiver(post_save, sender=Like)
def like_post_save(sender, instance, created, **kwargs):
    """
    当用户收到点赞时发送通知
    """
    if created:
        # 获取照片所有者
        photo_owner = instance.photo.uploaded_by
        
        # 不给自己发通知
        if photo_owner != instance.user:
            # 创建通知
            Notification.objects.create(
                recipient=photo_owner,
                sender=instance.user,
                notification_type='like',
                content=f'{instance.user.username} 点赞了你的照片',
                related_object_id=instance.id
            )


@receiver(post_save, sender=Favorite)
def favorite_post_save(sender, instance, created, **kwargs):
    """
    当用户收到收藏时发送通知
    """
    if created:
        # 获取照片所有者
        photo_owner = instance.photo.uploaded_by
        
        # 不给自己发通知
        if photo_owner != instance.user:
            # 创建通知
            Notification.objects.create(
                recipient=photo_owner,
                sender=instance.user,
                notification_type='favorite',
                content=f'{instance.user.username} 收藏了你的照片',
                related_object_id=instance.id
            )


@receiver(post_save, sender=CommentLike)
def comment_like_post_save(sender, instance, created, **kwargs):
    """
    当用户收到评论点赞时发送通知
    """
    if created:
        # 获取评论所有者
        comment_owner = instance.comment.user
        
        # 不给自己发通知
        if comment_owner != instance.user:
            # 创建通知
            Notification.objects.create(
                recipient=comment_owner,
                sender=instance.user,
                notification_type='comment_like',
                content=f'{instance.user.username} 点赞了你的评论',
                related_object_id=instance.id
            )