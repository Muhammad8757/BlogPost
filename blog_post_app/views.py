from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from .serializers import FavoriteSerializer, PostCreateUpdateSerializer, PostSerializer, UserSerializer, CommentSerializer, LikedSerializer
from .models import Post, User, Comment, Liked, Favorite
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action
from .functions import AuthenticatedMixin, average_rating, is_auth, is_user_id_1
@extend_schema(tags=['User'])
class UserAPIView(GenericViewSet):
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

@extend_schema(tags=['Post'])
class PostAPIView(AuthenticatedMixin,
                   GenericViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    @extend_schema(
    parameters=[
        OpenApiParameter(name='title',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='content',location=OpenApiParameter.QUERY, required=True, type=str),
        OpenApiParameter(name='description',location=OpenApiParameter.QUERY, required=True, type=str),
        ],
        request=None
    )
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
            return Response({"detail": "not enough rights to update a post."}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
    request=PostCreateUpdateSerializer,
    responses={201: PostSerializer}
    )
    def create(self, request):
        is_user_id_1(request)
        serializer = PostCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        validated_data = serializer.validated_data
        validated_data['user'] = request.user
        post = serializer.create(validated_data)
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        
    def list(self, request):
        posts_info = Post.objects.all().values('id', 'title', 'description', 'user', 'created_at', 'image')
        posts = []
        ratings = {}
        posts_list = list(posts_info)
        for post in posts_list:
            post_id = post['id']
            ratings[post_id] = average_rating(post_id)
        for post in posts_list:
            post_id = post['id']
            data = {
                'id': post['id'],
                'title': post['title'],
                'description': post['description'],
                'user': post['user'],
                'created_at': post['created_at'],
                'image': post['image'],
                'rating': ratings.get(post_id, 0)
            }
            posts.append(data)
        
        return Response(posts)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        post_data = PostCreateUpdateSerializer(instance).data
        post_data.update({
            'raiting': average_rating(instance.id),
            'comments': CommentSerializer(Comment.objects.filter(post=instance), many=True).data,
            'liked': LikedSerializer(Liked.objects.filter(post=instance), many=True).data,
        })
        return Response(post_data)
    
    def destroy(self, request, *args, **kwargs):
        is_user_id_1(request)
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Comment'])
class CommentAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def list(self, request, *args, **kwargs):
        comments = Comment.objects.all().values('id', 'post', 'content', 'created_at', 'user')
        comments_with_users = []
        for comment in comments:
            user_id = comment.get('user')
            user_data = User.objects.filter(id=user_id).values('id', 'name').first()
            comment_with_user = {
                'id': comment['id'],
                'content': comment['content'],
                'post': comment['post'],
                'created_at': comment['created_at'],
                'user': {
                    'user_id': user_data.get('id') if user_data else None,
                    'user_name': user_data.get('name') if user_data else None
                }
            }
            comments_with_users.append(comment_with_user)
        response_data = {
            'comments': comments_with_users
        }
        return Response(response_data, status=status.HTTP_200_OK)

        
    @extend_schema(
        parameters=[
            OpenApiParameter(name='content', location=OpenApiParameter.QUERY, required=True, type=str),
            OpenApiParameter(name='post', location=OpenApiParameter.QUERY, required=True, type=int),
        ],
        request=None
    )
    def update(self, request, *args, **kwargs):
        is_auth(request)
        content = request.query_params.get('content', None)
        post = request.query_params.get('post', None)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = CommentSerializer(instance, data={'content': content, 'post': post, 'user': request.user.id}, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='post', location=OpenApiParameter.QUERY, required=True, type=int),
            OpenApiParameter(name='content', location=OpenApiParameter.QUERY, required=True, type=str),
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
@extend_schema(tags=['Liked'])
class LikedVAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Liked.objects.all()
    serializer_class = LikedSerializer

    @extend_schema(
    parameters=[
        OpenApiParameter(name='grade',location=OpenApiParameter.QUERY, required=True, type=int),
        OpenApiParameter(name='post',location=OpenApiParameter.QUERY, required=True, type=int),
        ],
        request=None
    )
    def create(self, request):
        is_auth(request)
        grade = request.query_params.get('grade', None)
        post = request.query_params.get('post', None)
        serializer = LikedSerializer(data={'grade': grade, 'post': post, 'user': request.user.id})
        serializer.is_valid(raise_exception=True)
        is_rated = Liked.objects.filter(user_id=self.request.user, post_id=post).exists()
        if is_rated:
            return Response({"detail": "You can't rate a post more than once."}, status=status.HTTP_400_BAD_REQUEST)
        liked = serializer.save()
        return Response(
            {
                'success': LikedSerializer(liked).data
            }
        )        
    
@extend_schema(tags=['Favorite'])
class FavoriteAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = FavoriteSerializer
        
    @extend_schema(
    parameters=[
        OpenApiParameter(name='post', location=OpenApiParameter.QUERY, required=True, type=int),
    ],
    request=None
    )
    def create(self, request):
        post_id = request.query_params.get('post')
        favorite = Favorite.objects.filter(user=request.user).first()
        
        if favorite and favorite.posts.filter(id=post_id).exists():
            return Response({"detail": "You can't favorite a post twice."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = FavoriteSerializer(data={'posts': [post_id], 'user': request.user.id})
        serializer.is_valid(raise_exception=True)
        favorite_save = serializer.save()
        
        return Response({
            'success': FavoriteSerializer(favorite_save).data
        })

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)