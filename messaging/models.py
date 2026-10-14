from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Une conversation privée entre 2 utilisateurs.
    On stocke toujours le participant avec l'ID le plus petit en premier
    pour éviter les doublons (user1-user2 et user2-user1 = même conv).
    """
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_p2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('participant1', 'participant2')

    def __str__(self):
        return f"Conv #{self.id} : {self.participant1.username} ↔ {self.participant2.username}"

    @staticmethod
    def find_or_create(user_a, user_b):
        """Trouve ou crée une conversation entre 2 users (ordre peu importe)"""
        # Toujours mettre le plus petit ID en premier
        if user_a.id > user_b.id:
            user_a, user_b = user_b, user_a

        conv, created = Conversation.objects.get_or_create(
            participant1=user_a,
            participant2=user_b
        )
        return conv, created

    def other_user(self, me):
        """Renvoie l'autre participant (pas moi)"""
        return self.participant2 if self.participant1 == me else self.participant1


class Message(models.Model):
    """Un message dans une conversation"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']  # du plus ancien au plus récent

    def __str__(self):
        return f"{self.sender.username} : {self.content[:30]}"