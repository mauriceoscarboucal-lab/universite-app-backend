from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    filiere = models.CharField(max_length=100, blank=True)
    niveau = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # ⬇️ NOUVEAU : vérification email
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_expires = models.DateTimeField(null=True, blank=True)
    # ⬇️ NOUVEAU : profil complété
    profile_completed = models.BooleanField(default=False)

class Follow(models.Model):
    """
    Représente un abonnement : follower suit following.
    - follower  = celui qui suit
    - following = celui qui est suivi
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} suit {self.following.username}"