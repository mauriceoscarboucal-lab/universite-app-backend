from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'likes_count', 'comments_count')
    search_fields = ('author__username', 'content')
    list_filter = ('created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at')
    search_fields = ('author__username', 'content')