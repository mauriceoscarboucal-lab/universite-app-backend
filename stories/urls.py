from django.urls import path
from .views import (
    StoryListCreateView,
    StoryDetailView,
    MyStoriesView,
    MarkStoryViewedView,
    StoryViewersView,
)

urlpatterns = [
    path('', StoryListCreateView.as_view(), name='story_list_create'),
    path('mine/', MyStoriesView.as_view(), name='my_stories'),
    path('<int:story_id>/', StoryDetailView.as_view(), name='story_detail'),
    path('<int:story_id>/view/', MarkStoryViewedView.as_view(), name='mark_viewed'),
    path('<int:story_id>/viewers/', StoryViewersView.as_view(), name='story_viewers'),
]