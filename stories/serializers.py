from rest_framework import serializers
from .models import Story, StoryView


class StorySerializer(serializers.ModelSerializer):
    """Une story avec les infos de son auteur + nombre de vues"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_photo = serializers.ImageField(source='author.photo', read_only=True)
    views_count = serializers.SerializerMethodField()
    is_viewed = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'author', 'author_username', 'author_photo',
            'image', 'caption', 'created_at', 'expires_at',
            'views_count', 'is_viewed',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'expires_at']

    def get_views_count(self, obj):
        return obj.views.count()

    def get_is_viewed(self, obj):
        """Est-ce que l'utilisateur connecté a déjà vu cette story ?"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.views.filter(user=request.user).exists()
        return False


class StoryViewerSerializer(serializers.ModelSerializer):
    """Représente un utilisateur qui a vu une story"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    filiere = serializers.CharField(source='user.filiere', read_only=True)
    niveau = serializers.CharField(source='user.niveau', read_only=True)
    photo = serializers.ImageField(source='user.photo', read_only=True)

    class Meta:
        model = StoryView
        fields = ['id', 'user_id', 'username', 'filiere', 'niveau', 'photo', 'viewed_at']


class StoryGroupSerializer(serializers.Serializer):
    """Groupe de stories par auteur (comme Instagram)"""
    author_id = serializers.IntegerField()
    author_username = serializers.CharField()
    author_photo = serializers.ImageField(allow_null=True)
    stories = StorySerializer(many=True)
    all_viewed = serializers.BooleanField()