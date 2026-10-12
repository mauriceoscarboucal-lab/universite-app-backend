from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Story(models.Model):
    """
    Une story publiée par un étudiant, visible 24h seulement.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories'
    )
    image = models.ImageField(upload_to='stories/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # À la création, on définit l'expiration à +24h
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Story de {self.author.username} - {self.created_at:%d/%m %H:%M}"