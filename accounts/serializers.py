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
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'filiere', 'niveau', 'photo', 'bio']
        read_only_fields = ['id', 'email']