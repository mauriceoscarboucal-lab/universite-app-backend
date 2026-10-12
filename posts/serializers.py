from rest_framework import serializers
from .models import Post, Like, Comment


class CommentSerializer(serializers.ModelSerializer):
    """Affiche les infos d'un commentaire"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_photo = serializers.ImageField(source='author.photo', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_username', 'author_photo', 'post', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'post', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """Affiche une publication complète"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_photo = serializers.ImageField(source='author.photo', read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_photo',
            'content', 'image',
            'likes_count', 'comments_count', 'is_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        """Est-ce que l'utilisateur connecté a liké ce post ?"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False