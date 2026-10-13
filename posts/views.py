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
        post = serializer.save(author=self.request.user)
        images = self.request.FILES.getlist('images')
        if images:
            urls = []
            for img in images:
                from django.core.files.storage import default_storage
                path = default_storage.save(f'posts/{img.name}', img)
                url = default_storage.url(path)
                urls.append(url)
            post.images = urls
            post.save()
    
    def destroy(self, request, *args, **kwargs):
        """Seul l'auteur peut supprimer son post"""
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {'error': 'Tu ne peux pas supprimer ce post'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

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