from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Story, StoryView
from .serializers import (
    StorySerializer,
    StoryGroupSerializer,
    StoryViewerSerializer,
)


class StoryListCreateView(APIView):
    """
    GET : liste des stories non expirées, groupées par auteur
    POST : créer une nouvelle story
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # On garde -created_at pour trier les UTILISATEURS (les plus récents en premier dans la barre)
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
                    'all_viewed': True,
                }
            grouped[story.author.id]['stories'].append(story)

        # 🔄 INVERSION : on met les stories du plus ANCIEN au plus RÉCENT
        # (comme ça quand on ouvre, on commence par la première publiée)
        for group in grouped.values():
            group['stories'].reverse()

        # On calcule "all_viewed"
        for group in grouped.values():
            stories_list = group['stories']
            all_seen = all(
                s.views.filter(user=request.user).exists()
                for s in stories_list
            )
            group['all_viewed'] = all_seen

        result = list(grouped.values())

        serializer = StoryGroupSerializer(
            result,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = StorySerializer(
            data=request.data,
            context={'request': request}
        )
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
        serializer = StorySerializer(story, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
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
        serializer = StorySerializer(
            stories,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class MarkStoryViewedView(APIView):
    """
    Marque une story comme vue par l'utilisateur connecté.
    Appelé automatiquement quand quelqu'un ouvre une story.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si c'est ma propre story, je ne la marque pas comme vue
        if story.author == request.user:
            return Response({'status': 'own_story'})

        # Crée ou ignore si déjà vue
        view, created = StoryView.objects.get_or_create(
            user=request.user,
            story=story
        )

        return Response({
            'status': 'created' if created else 'already_viewed',
            'views_count': story.views.count(),
        })


class StoryViewersView(APIView):
    """
    Liste des utilisateurs qui ont vu une story.
    Seul le propriétaire peut voir cette liste.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id)
        except Story.DoesNotExist:
            return Response(
                {'error': 'Story introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        if story.author != request.user:
            return Response(
                {'error': 'Tu ne peux pas voir les vues de cette story'},
                status=status.HTTP_403_FORBIDDEN
            )

        views = story.views.select_related('user').all()
        serializer = StoryViewerSerializer(views, many=True)
        return Response(serializer.data)