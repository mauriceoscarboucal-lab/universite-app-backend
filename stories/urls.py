from django.urls import path
from .views import StoryListCreateView, StoryDetailView, MyStoriesView

urlpatterns = [
    path('', StoryListCreateView.as_view(), name='story_list_create'),
    path('mine/', MyStoriesView.as_view(), name='my_stories'),
    path('<int:story_id>/', StoryDetailView.as_view(), name='story_detail'),
]