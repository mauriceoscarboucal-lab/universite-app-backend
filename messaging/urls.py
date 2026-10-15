from django.urls import path
from .views import (
    ConversationListView,
    MessageListView,
    UnreadCountView,
    MessageDetailView,
)

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message_list'),
    path('messages/<int:message_id>/', MessageDetailView.as_view(), name='message_detail'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
]