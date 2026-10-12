from django.db.models import Q
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Story
from .serializers import StorySerializer, StoryGroupSerializer


class StoryListCreateView(APIView):
    """
    GET : liste des stories non expirées, groupées par auteur
    POST : créer une nouvelle story
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # On récupère toutes les stories non expirées
        stories = Story.objects.filter(
            expires_at__gt=timezone.now()
        ).select_related('author').order_by('-created_at')

        # On les groupe par auteur
        grouped = {}
        for story in stories:
            if story.author.id not in grouped:
                grouped[story.author.id] = {
                    'author_id': story.author.id,
                    'author_username': story.author.username,
                    'author_photo': story.author.photo,
                    'stories': [],
                }
            grouped[story.author.id]['stories'].append(story)

        # On transforme en liste
        result = list(grouped.values())

        # On sérialise
        serializer = StoryGroupSerializer(result, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoryDetailView(APIView):
    """Voir ou supprimer une story"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = StorySerializer(story)
        return Response(serializer.data)

    def delete(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        # Seul l'auteur peut supprimer
        if story.author != request.user:
            return Response(
                {'error': 'Tu ne peux pas supprimer cette story'},
                status=status.HTTP_403_FORBIDDEN
            )
        story.delete()
        return Response({'status': 'deleted'})


class MyStoriesView(APIView):
    """Voir ses propres stories"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stories = Story.objects.filter(
            author=request.user,
            expires_at__gt=timezone.now()
        )
        serializer = StorySerializer(stories, many=True)
        return Response(serializer.data)