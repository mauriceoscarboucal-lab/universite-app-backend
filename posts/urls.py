from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, NotificationListView

router = DefaultRouter()
# ⚠️ On garde le préfixe 'posts' pour que l'API réponde sur /api/posts/
router.register('posts', PostViewSet, basename='post')

urlpatterns = [
    # ⚠️ L'URL pour les notifications sera /api/posts/notifications/
    path('posts/notifications/', NotificationListView.as_view(), name='notifications'),
    path('', include(router.urls)),
]