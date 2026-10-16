from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend d'authentification qui accepte :
    - soit l'email
    - soit le username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')

        if username is None or password is None:
            return None

        # Essaie par email d'abord
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Sinon essaie par username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None