from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from .serializers import FeaturedSerializer, PostSerializer, UserSerializer, CommentSerializer, FavoriteSerializer
from .models import Post, User, Comment, Favorite, Featured
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action, permission_classes, authentication_classes

def is_auth(request):
    if not request.user.id:
        raise Exception("user not authentificated")

class UserAPIView(mixins.CreateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
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
    parameters=[
        OpenApiParameter(name='phone_number',location=OpenApiParameter.QUERY, required=True, type=int),
        OpenApiParameter(name='password',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        phone_number = request.query_params.get('phone_number', None)
        password = request.query_params.get('password', None)
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

class PostAPIView(mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def average_rating(self):
        posts = Post.objects.filter(user=1).values_list('id', flat=True)
        grade = Favorite.objects.filter(post_id__in=posts).values_list('grade', flat=True)
        peoples = Favorite.objects.filter(post_id__in=posts).values_list('peoples_grade', flat=True)
        grade_list = list(grade)
        peoples_list = list(peoples)
        if not peoples:
            return 0
        return sum(grade_list) / len(peoples_list)
    
    @extend_schema(
    parameters=[
        OpenApiParameter(name='title',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='content',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='description',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def update(self, request, **kwargs): #этот метод из исходника класса UpdateModelMixin
        if request.user == User.objects.get(id=1):
            is_auth(request)
            title = request.query_params.get('title', None)
            description = request.query_params.get('description', None)
            content = request.query_params.get('content', None)
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data={'title': title, 'content': content, 'description': description, 'user': request.user.id}, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)
        else:
            raise Exception("not enough rights to update a post")
        

    @extend_schema(
    parameters=[
        OpenApiParameter(name='title',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='content',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='description',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def create(self, request):
        if request.user == User.objects.get(id=1):
            is_auth(request)
            title = request.query_params.get('title', None)
            description = request.query_params.get('description', None)
            content = request.query_params.get('content', None)
            serializer = PostSerializer(data={'title': title, 'content': content, 'description': description, 'user': request.user.id})
            serializer.is_valid(raise_exception=True)
            post = serializer.save()
            return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        else:
            raise Exception("not enough rights to create a post")
        
    def list(self, request):
        posts = Post.objects.all()
        raiting = self.average_rating()
        return Response({
            "posts": self.get_serializer(posts, many=True).data,
            'raiting': raiting,
            'comments': CommentSerializer(Comment.objects.all(), many=True).data,
            'rated': FavoriteSerializer(Favorite.objects.all(), many=True).data
            })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(
            {
                'post': PostSerializer(instance).data,
                'comment': CommentSerializer(Comment.objects.filter(post=instance), many=True).data,
                'liked': FavoriteSerializer(Favorite.objects.filter(post=instance), many=True).data,
            })
    

    
class CommentAPIView(mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='content', location=OpenApiParameter.QUERY, required=True, type=str),
            OpenApiParameter(name='post', location=OpenApiParameter.QUERY, required=True, type=int),
        ],
        request=None
    )
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def update(self, request, *args, **kwargs):
        is_auth(request)
        content = request.query_params.get('content', None)
        post = request.query_params.get('post', None)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = CommentSerializer(instance, data={'content': content, 'post': post,'user': request.user.id}, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)
    
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    @extend_schema(
    parameters=[
        OpenApiParameter(name='post',location=OpenApiParameter.QUERY, required=True, type=int),
        OpenApiParameter(name='content',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
    def create(self, request):
        is_auth(request)
        post = request.query_params.get('post', None)
        content = request.query_params.get('content', None)
        serializer = CommentSerializer(data={'content': content, 'post': post, 'user': request.user.id})
        serializer.is_valid(raise_exception=True)
        favorite = serializer.save()
        return Response(
            {
                'success': CommentSerializer(favorite).data
            }
        )

class FavoriteAPIView(mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = FavoriteSerializer
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    @extend_schema(
    parameters=[
        OpenApiParameter(name='grade',location=OpenApiParameter.QUERY, required=True, type=int),
        OpenApiParameter(name='post',location=OpenApiParameter.QUERY, required=True, type=int),
        ],
        request=None
    )
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def create(self, request):
        is_auth(request)
        grade = request.query_params.get('grade', None)
        post = request.query_params.get('post', None)
        serializer = FavoriteSerializer(data={'grade': grade, 'post': post, 'user': request.user.id})
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
        
class FeaturedAPIView(mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = FeaturedSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context
        
    @extend_schema(
    parameters=[
        OpenApiParameter(name='post', location=OpenApiParameter.QUERY, required=True, type=int),
    ],
    request=None
    )
    @authentication_classes([JWTAuthentication])
    @permission_classes([IsAuthenticated])
    def create(self, request):
        post_id = request.query_params.get('post')
        featured = Featured.objects.filter(user=request.user).first()
        
        if featured and featured.posts.filter(id=post_id).exists():
            raise Exception("You can't favorite a post twice")
        
        serializer = FeaturedSerializer(data={'posts': [post_id], 'user': request.user.id})
        serializer.is_valid(raise_exception=True)
        featured_save = serializer.save()
        
        return Response({
            'success': FeaturedSerializer(featured_save).data
        })

    def get_queryset(self):
        return Featured.objects.filter(user=self.request.user)