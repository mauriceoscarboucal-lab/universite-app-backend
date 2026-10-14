from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()


class ConversationListView(APIView):
    """
    GET  : liste des conversations de l'utilisateur connecté
    POST : créer (ou récupérer) une conversation avec un autre utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            participant1=request.user
        ) | Conversation.objects.filter(
            participant2=request.user
        )
        conversations = conversations.order_by('-updated_at')

        serializer = ConversationSerializer(
            conversations,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    def post(self, request):
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response(
                {'error': 'user_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if int(other_user_id) == request.user.id:
            return Response(
                {'error': 'Tu ne peux pas discuter avec toi-même'},
                status=status.HTTP_400_BAD_REQUEST
            )

        other_user = get_object_or_404(User, id=other_user_id)
        conv, created = Conversation.find_or_create(request.user, other_user)

        serializer = ConversationSerializer(
            conv,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class MessageListView(APIView):
    """
    GET  : liste des messages d'une conversation
    POST : envoyer un message dans la conversation
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)

        # Vérifier que je fais partie de cette conversation
        if request.user not in (conv.participant1, conv.participant2):
            return Response(
                {'error': 'Accès refusé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Marquer les messages reçus comme lus
        conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        messages = conv.messages.select_related('sender').all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)

        if request.user not in (conv.participant1, conv.participant2):
            return Response(
                {'error': 'Accès refusé'},
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'Le message ne peut pas être vide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        message = Message.objects.create(
            conversation=conv,
            sender=request.user,
            content=content,
        )

        # Mettre à jour la date de la conversation pour la remonter
        conv.save()

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)