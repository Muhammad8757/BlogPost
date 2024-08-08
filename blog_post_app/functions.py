from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .models import Liked, User

def is_auth(request):
    if not request.user.id:
        #! Название функции и его задача не сходятся
        return Response({"detail": "user not authentificated."}, status=status.HTTP_400_BAD_REQUEST)

class AuthenticatedMixin:
    #! Бесполезный миксин. Совсем не нужен.
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [permission() for permission in [IsAuthenticated]]
        return []

def average_rating(post_id):
        grade = Liked.objects.filter(post_id=post_id).values_list('grade', flat=True)
        peoples = Liked.objects.filter(post_id=post_id).values_list('peoples_grade', flat=True)
        grade_list = list(grade)
        peoples_list = list(peoples)
        if not peoples:
            return 0
        return sum(grade_list) / len(peoples_list)

def is_user_id_1(request):
    #! Нет нет и нет. Так вообще нельзя!!!!!!!!!!!!!!!!!!!!!!!
    if request.user.id != 1:
        raise Exception("Not enough rights to create a post.")