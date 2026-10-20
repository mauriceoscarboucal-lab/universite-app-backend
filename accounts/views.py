from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from posts.models import Notification

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserPublicSerializer,
)
from .models import Follow

User = get_user_model()

class EmailTokenObtainPairView(TokenObtainPairView):
    """Vue de login qui utilise email au lieu de username"""
    serializer_class = EmailTokenObtainPairSerializer

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
            # Optionnel : supprimer la notification si on se désabonne
            Notification.objects.filter(sender=request.user, recipient=target, notification_type='follow').delete()
            return Response({
                'status': 'unfollowed',
                'followers_count': target.followers.count(),
            })
        
        # 🔔 Créer la notification d'abonnement
        Notification.objects.create(
            recipient=target,
            sender=request.user,
            notification_type='follow'
        )
        
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

class UserSearchView(APIView):
    """Recherche d'utilisateurs par nom ou filière"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()

        if not query:
            users = User.objects.exclude(id=request.user.id)[:50]
        else:
            users = User.objects.filter(
                Q(username__iexact=query) |      # Correspondance EXACTE (insensible à la casse)
                Q(username__icontains=query) |   # Recherche partielle
                Q(filiere__icontains=query) |
                Q(niveau__icontains=query)
            ).exclude(id=request.user.id)

            # On trie pour mettre les correspondances exactes en premier
            users = sorted(
                users,
                key=lambda u: u.username.lower() != query.lower()
            )[:50]

        serializer = UserPublicSerializer(users, many=True)
        return Response(serializer.data)

import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings


class SendVerificationCodeView(APIView):
    """Envoie un code de vérification à 6 chiffres par email"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.email_verified:
            return Response({'status': 'already_verified'})

        # Génère un code à 6 chiffres
        code = str(random.randint(100000, 999999))
        user.verification_code = code
        user.verification_expires = timezone.now() + timedelta(minutes=15)
        user.save()

        # Envoie l'email
        try:
            send_mail(
                subject='Baobab - Vérifie ton email',
                message=f'''
Salut {user.first_name or user.username} !

Bienvenue sur Baobab 🌳

Voici ton code de vérification : {code}

Il est valable 15 minutes.

L'équipe Baobab
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response({'status': 'sent', 'email': user.email})
        except Exception as e:
            return Response(
                {'error': f'Erreur envoi email : {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailView(APIView):
    """Vérifie le code et marque l'email comme vérifié"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get('code', '').strip()

        if not code:
            return Response(
                {'error': 'Code requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.email_verified:
            return Response({'status': 'already_verified'})

        if not user.verification_code:
            return Response(
                {'error': 'Aucun code envoyé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() > user.verification_expires:
            return Response(
                {'error': 'Code expiré. Renvoie un nouveau code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if code != user.verification_code:
            return Response(
                {'error': 'Code incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Vérifié !
        user.email_verified = True
        user.verification_code = ''
        user.verification_expires = None
        user.save()

        return Response({'status': 'verified'})


class CompleteProfileView(APIView):
    """Marque le profil comme complété"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.profile_completed = True

        # On met à jour ce que l'utilisateur a envoyé
        if 'bio' in request.data:
            user.bio = request.data['bio']
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']

        user.save()
        return Response({'status': 'profile_completed'})

class UploadPhotoView(APIView):
    """Permet à l'utilisateur de mettre à jour sa photo de profil"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if 'photo' not in request.FILES:
            return Response(
                {'error': 'Aucune photo fournie'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.photo = request.FILES['photo']
        user.save()

        return Response({
            'status': 'photo_updated',
            'photo_url': user.photo.url if user.photo else None
        })