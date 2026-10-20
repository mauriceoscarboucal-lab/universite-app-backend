from django.db import models
from django.conf import settings


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    images = models.JSONField(default=list, blank=True)   # <-- AJOUTE (liste URLs)
    background_color = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Couleur de fond pour les posts texte'
    )
    # ⬇️ NOUVEAUX CHAMPS
    audience = models.CharField(max_length=20, default='public') # public, followers, private
    hashtags = models.JSONField(default=list, blank=True) # Liste des hashtags
    mentions = models.JSONField(default=list, blank=True) # Liste des usernames mentionnés
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # les plus récents en premier

    def __str__(self):
        return f"Post de {self.author.username} - {self.created_at:%d/%m/%Y}"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()


class Like(models.Model):
    """Un like sur une publication. Un utilisateur ne peut liker qu'une fois."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 1 like max par user par post

    def __str__(self):
        return f"{self.user.username} aime le post {self.post.id}"


class Comment(models.Model):
    """Un commentaire sur une publication"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # du plus ancien au plus récent

    def __str__(self):
        return f"Commentaire de {self.author.username}"

class Notification(models.Model):
    TYPES = (
        ('like', 'Like'),
        ('comment', 'Commentaire'),
        ('follow', 'Abonnement'),
    )
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']