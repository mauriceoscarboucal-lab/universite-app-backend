from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_id', 'sender_username',
            'content', 'created_at', 'is_read', 'is_delivered',
            'deleted_for_all', 'deleted_for', 'edited',
        ]
        read_only_fields = [
            'id', 'sender', 'created_at', 'is_read', 'is_delivered',
            'deleted_for_all', 'deleted_for', 'edited',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Une conversation avec l'autre utilisateur + dernier message"""
    other_user_id = serializers.SerializerMethodField()
    other_username = serializers.SerializerMethodField()
    other_photo = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()      # <-- AJOUTE
    follows_me = serializers.SerializerMethodField()        # <-- AJOUTE

    class Meta:
        model = Conversation
        fields = [
            'id', 'other_user_id', 'other_username', 'other_photo',
            'last_message', 'unread_count', 'updated_at',
            'is_following', 'follows_me',                    # <-- AJOUTE
        ]

    def get_other_user_id(self, obj):
        me = self.context['request'].user
        return obj.other_user(me).id

    def get_other_username(self, obj):
        me = self.context['request'].user
        return obj.other_user(me).username

    def get_other_photo(self, obj):
        me = self.context['request'].user
        other = obj.other_user(me)
        if other.photo:
            return other.photo.url
        return None

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                'content': last.content,
                'sender_id': last.sender.id,
                'created_at': last.created_at,
                'is_read': last.is_read,           # <-- AJOUTE
                'is_delivered': last.is_delivered, # <-- AJOUTE
            }
        return None

    def get_unread_count(self, obj):
        me = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=me).count()

    def get_is_following(self, obj):
        """Est-ce que moi je suis l'autre ?"""
        me = self.context['request'].user
        other = obj.other_user(me)
        from accounts.models import Follow
        return Follow.objects.filter(
            follower=me, following=other
        ).exists()

    def get_follows_me(self, obj):
        """Est-ce que l'autre me suit ?"""
        me = self.context['request'].user
        other = obj.other_user(me)
        from accounts.models import Follow
        return Follow.objects.filter(
            follower=other, following=me
        ).exists()