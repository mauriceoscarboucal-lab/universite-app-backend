from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Post, Like, Comment
from .serializers import PostSerializer, CommentSerializer


class PostViewSet(viewsets.ModelViewSet):
    """CRUD complet des publications + like"""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.select_related('author').prefetch_related('likes', 'comments')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()
            status_str = 'unliked'
        else:
            status_str = 'liked'

        # ⚠️ Recharger le post depuis la base pour avoir le bon compte
        post.refresh_from_db()

        return Response({
            'status': status_str,
            'likes_count': post.likes.count()
        })

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == 'GET':
            comments = post.comments.select_related('author').all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)