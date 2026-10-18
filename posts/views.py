from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Post, Like, Comment, Notification
from .serializers import PostSerializer, CommentSerializer, NotificationSerializer


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
            # Optionnel : supprimer la notification si on retire le like
            Notification.objects.filter(sender=request.user, recipient=post.author, post=post, notification_type='like').delete()
        else:
            status_str = 'liked'
            # 🔔 Créer la notification si ce n'est pas mon propre post
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='like',
                    post=post
                )

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

                # POST → créer un commentaire
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            # 🔔 Créer la notification
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Marquer tout comme lu
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'read'})