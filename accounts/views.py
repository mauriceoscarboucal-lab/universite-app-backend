from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserPublicSerializer,
)
from .models import Follow

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel étudiant"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    """Voir/modifier son propre profil"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """Voir le profil public d'un autre étudiant"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserPublicSerializer(user)
        # Est-ce que MOI je suis cet utilisateur ?
        is_following = Follow.objects.filter(
            follower=request.user, following=user
        ).exists()
        return Response({
            **serializer.data,
            'is_following': is_following,
            'is_me': request.user.id == user.id,
        })


class FollowToggleView(APIView):
    """Suivre ou ne plus suivre un utilisateur"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, id=user_id)

        if target.id == request.user.id:
            return Response(
                {'error': 'Tu ne peux pas te suivre toi-même'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user, following=target
        )

        if not created:
            follow.delete()
            return Response({
                'status': 'unfollowed',
                'followers_count': target.followers.count(),
            })
        return Response({
            'status': 'followed',
            'followers_count': target.followers.count(),
        })


class UserPostsView(generics.ListAPIView):
    """Liste les posts d'un utilisateur"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None  # On le remplit dans get_serializer_class

    def get_serializer_class(self):
        from posts.serializers import PostSerializer
        return PostSerializer

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        from posts.models import Post
        user_id = self.kwargs['user_id']
        return Post.objects.filter(author_id=user_id).select_related('author')

class UserFollowersView(APIView):
    """Liste des abonnés d'un utilisateur"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        followers = User.objects.filter(following__following=user)
        serializer = UserPublicSerializer(followers, many=True)
        return Response(serializer.data)


class UserFollowingView(APIView):
    """Liste des abonnements d'un utilisateur"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        following = User.objects.filter(followers__follower=user)
        serializer = UserPublicSerializer(following, many=True)
        return Response(serializer.data)