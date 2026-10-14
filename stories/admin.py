from django.contrib import admin
from .models import Story, StoryView


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('created_at',)
    search_fields = ('author__username',)


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'story', 'viewed_at')
    search_fields = ('user__username',)