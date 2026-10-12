from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, ProfileView

urlpatterns = [
    # Inscription
    path('register/', RegisterView.as_view(), name='register'),

    # Connexion (retourne un token JWT)
    path('login/', TokenObtainPairView.as_view(), name='login'),

    # Rafraîchir le token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profil (utilisateur connecté)
    path('me/', ProfileView.as_view(), name='profile'),
]