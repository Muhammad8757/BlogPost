from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from .serializers import PostSerializer, UserSerializer, CommentSerializer, FavoriteSerializer
from .models import Post, User, Comment, Favorite
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework.decorators import action




class UserAPIView(mixins.CreateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Successful login"
            ),
            400: 'Invalid input',
            404: 'User not found'
        }
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if phone_number and password:
            try:
                user = User.objects.get(phone_number=phone_number)
                
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    })
                else:
                    return Response({"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "Phone number and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        


class PostAPIView(mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    @action(detail=False, methods=['get'])
    def average_rating(self, request):
        posts = Post.objects.filter(user=request.user).values_list('id', flat=True)
        grade = Favorite.objects.filter(post_id__in=posts).values_list('grade', flat=True)
        peoples = Favorite.objects.filter(post_id__in=posts).values_list('peoples_grade', flat=True)
        grade_list = list(grade)
        peoples_list = list(peoples)
        sum_grade = sum(grade_list)
        count_peoples = len(peoples_list)
        if count_peoples == 0:
            return Response(data={
            "average rating": 0
            })
        return Response(data={
            "average rating": sum_grade/count_peoples
            })


    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    
    @extend_schema(
    parameters=[
        OpenApiParameter(name='title',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='content',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
    def create(self, request):
        context = self.get_serializer_context()
        title = request.query_params.get('title', None)
        content = request.query_params.get('content', None)
        serializer = PostSerializer(data={'title': title, 'content': content}, context=context)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        return Response(PostSerializer(transaction).data, status=status.HTTP_201_CREATED)
    
    
class CommentAPIView(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = CommentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    
    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)
    
class FavoriteAPIView(mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = FavoriteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    @extend_schema(
    parameters=[
        OpenApiParameter(name='grade',location=OpenApiParameter.QUERY, required=True, type=int),
        OpenApiParameter(name='post',location=OpenApiParameter.QUERY, required=True, type=int),
        ],
        request=None
    )
    def create(self, request):
        grade = request.query_params.get('grade', None)
        post = request.query_params.get('post', None)
        serializer = FavoriteSerializer(data={'grade': grade, 'post': post}, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        self.is_rated_user(request)
        favorite = serializer.save()
        return Response(
            {
                'success': FavoriteSerializer(favorite).data
            }
        )
        
    def is_rated_user(self, request):
        post_id_from_request = request.query_params.get('post')
        is_rated = Favorite.objects.filter(user_id=self.request.user, post_id=post_id_from_request).exists()
        if is_rated:
            raise Exception("You can't rate one post more than once.")
        