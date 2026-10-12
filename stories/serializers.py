from rest_framework import serializers
from .models import Story


class StorySerializer(serializers.ModelSerializer):
    """Une story avec les infos de son auteur"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_photo = serializers.ImageField(source='author.photo', read_only=True)

    class Meta:
        model = Story
        fields = [
            'id', 'author', 'author_username', 'author_photo',
            'image', 'caption', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'expires_at']


class StoryGroupSerializer(serializers.Serializer):
    """
    Groupe de stories par utilisateur (comme Instagram : tous les stories d'un user ensemble)
    """
    author_id = serializers.IntegerField()
    author_username = serializers.CharField()
    author_photo = serializers.ImageField(allow_null=True)
    stories = StorySerializer(many=True)