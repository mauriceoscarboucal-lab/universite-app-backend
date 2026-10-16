from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import EmailTokenObtainPairView

from .views import (
    RegisterView, ProfileView, UserDetailView, FollowToggleView,
    UserPostsView, UserFollowersView, UserFollowingView, UserSearchView,
    SendVerificationCodeView, VerifyEmailView, CompleteProfileView,
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', EmailTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profil
    path('me/', ProfileView.as_view(), name='profile'),

    # Recherche (⚠️ AVANT users/<int:user_id>)
    path('users/search/', UserSearchView.as_view(), name='user_search'),

    # Autres utilisateurs
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/follow/', FollowToggleView.as_view(), name='follow_toggle'),
    path('users/<int:user_id>/posts/', UserPostsView.as_view(), name='user_posts'),
    path('users/<int:user_id>/followers/', UserFollowersView.as_view(), name='user_followers'),
    path('users/<int:user_id>/following/', UserFollowingView.as_view(), name='user_following'),
    # ⬇️ NOUVELLES ROUTES
    path('send-verification/', SendVerificationCodeView.as_view(), name='send_verification'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('complete-profile/', CompleteProfileView.as_view(), name='complete_profile'),

]