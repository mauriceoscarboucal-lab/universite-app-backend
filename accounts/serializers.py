from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Sérializer pour l'inscription d'un étudiant"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'filiere', 'niveau']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Les deux mots de passe ne correspondent pas.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)   # chiffre le mot de passe
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Sérializer pour afficher les infos d'un utilisateur"""
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'filiere', 'niveau', 'photo', 'bio',
            'followers_count', 'following_count',
        ]
        read_only_fields = ['id', 'email']

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

from .models import Follow


class UserPublicSerializer(serializers.ModelSerializer):
    """Infos publiques d'un étudiant + compteurs de followers"""
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'filiere', 'niveau', 'photo', 'bio',
            'followers_count', 'following_count',
        ]

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()