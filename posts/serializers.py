from rest_framework import serializers
from .models import Post, Like, Comment
from .models import Post, Like, Comment, Notification


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
    is_following_author = serializers.SerializerMethodField()
    is_my_post = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_username', 'author_photo',
            'content', 'image',
            'images',
            'background_color',
            'likes_count', 'comments_count', 'is_liked',
            'is_following_author',
            'is_my_post',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'images']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_following_author(self, obj):
        """Est-ce que l'utilisateur connecté suit l'auteur du post ?"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from accounts.models import Follow
            return Follow.objects.filter(
                follower=request.user,
                following=obj.author
            ).exists()
        return False
    def get_is_my_post(self, obj):
        """Est-ce que ce post appartient à l'utilisateur connecté ?"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False

class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_photo = serializers.ImageField(source='sender.photo', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'sender_username', 'sender_photo', 'notification_type', 'post', 'is_read', 'created_at']