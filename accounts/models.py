from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour les étudiants.
    On étend le User par défaut de Django pour ajouter nos champs.
    """
    email = models.EmailField(unique=True)
    filiere = models.CharField(max_length=100, blank=True)
    niveau = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # L'email sera utilisé pour se connecter
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.email})"