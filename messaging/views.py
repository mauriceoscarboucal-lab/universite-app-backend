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

        # 📬 Quand on ouvre la liste des conversations,
        # on marque tous les messages reçus comme "delivered"
        for conv in conversations:
            conv.messages.filter(is_delivered=False).exclude(
                sender=request.user
            ).update(is_delivered=True)

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

        if request.user not in (conv.participant1, conv.participant2):
            return Response(
                {'error': 'Accès refusé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 📬 Marque delivered
        conv.messages.filter(is_delivered=False).exclude(sender=request.user).update(is_delivered=True)

        # 👁️ Marque read
        if request.query_params.get('read') == '1':
            conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        # 🚫 Filtre en Python (SQLite ne supporte pas contains sur JSON)
        all_messages = conv.messages.select_related('sender').all()
        my_id = request.user.id
        visible_messages = [
            m for m in all_messages
            if my_id not in (m.deleted_for or [])
        ]

        serializer = MessageSerializer(visible_messages, many=True)
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

class UnreadCountView(APIView):
    """
    Renvoie le nombre total de messages non lus pour l'utilisateur connecté.
    Utilisé pour afficher le badge rouge sur l'icône Messages.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Toutes mes conversations
        conversations = Conversation.objects.filter(
            participant1=request.user
        ) | Conversation.objects.filter(
            participant2=request.user
        )

        # Messages non lus (pas envoyés par moi)
        unread = Message.objects.filter(
            conversation__in=conversations,
            is_read=False,
        ).exclude(sender=request.user).count()

        return Response({'unread_count': unread})

class MessageDetailView(APIView):
    """
    DELETE : supprimer un message
       - ?scope=all  → supprimer pour tout le monde (seulement si c'est MON message)
       - ?scope=me   → supprimer pour moi seulement
    PATCH : modifier un message (seulement si c'est MON message)
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, message_id):
        try:
            msg = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Vérifier que je fais partie de la conversation
        conv = msg.conversation
        if request.user not in (conv.participant1, conv.participant2):
            return Response(
                {'error': 'Accès refusé'},
                status=status.HTTP_403_FORBIDDEN
            )

        scope = request.query_params.get('scope', 'me')

        if scope == 'all':
            # Supprimer pour tout le monde → seulement si c'est MON message
            if msg.sender != request.user:
                return Response(
                    {'error': 'Tu peux seulement supprimer tes propres messages pour tout le monde'},
                    status=status.HTTP_403_FORBIDDEN
                )
            msg.deleted_for_all = True
            msg.content = ''  # on efface le contenu
            msg.save()
            return Response({'status': 'deleted_for_all'})
        else:
            # Supprimer pour moi seulement
            deleted_list = msg.deleted_for or []
            if request.user.id not in deleted_list:
                deleted_list.append(request.user.id)
            msg.deleted_for = deleted_list
            msg.save()
            return Response({'status': 'deleted_for_me'})

    def patch(self, request, message_id):
        """Modifier le contenu d'un message (seulement si c'est MON message)"""
        try:
            msg = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        if msg.sender != request.user:
            return Response(
                {'error': 'Tu peux seulement modifier tes propres messages'},
                status=status.HTTP_403_FORBIDDEN
            )

        if msg.deleted_for_all:
            return Response(
                {'error': 'Ce message est supprimé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_content = request.data.get('content', '').strip()
        if not new_content:
            return Response(
                {'error': 'Le message ne peut pas être vide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        msg.content = new_content
        msg.edited = True
        msg.save()

        serializer = MessageSerializer(msg)
        return Response(serializer.data)