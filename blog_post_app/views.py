from rest_framework import mixins, status
from rest_framework.viewsets import GenericViewSet
from .serializers import FavoriteSerializer, LoginSerializer, PostCreateUpdateSerializer, PostSerializer, UserSerializer, CommentSerializer, LikedSerializer
from .models import Post, User, Comment, Liked, Favorite
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
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
    
    @extend_schema(request=LoginSerializer)
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']
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
    
    def update(self, request, **kwargs): #этот метод из исходника класса UpdateModelMixin
        if request.user == User.objects.get(id=1):
            is_auth(request)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({"detail": "not enough rights to update a post."}, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request):
        is_user_id_1(request)
        serializer = PostCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        validated_data = serializer.validated_data
        validated_data['user'] = request.user
        post = serializer.save()
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        
    def list(self, request):
        queryset = Post.objects.all()
        serializer = PostSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        post_data = PostSerializer(instance).data
        post_data.update({
            'raiting': average_rating(instance.id),
            'comments': CommentSerializer(Comment.objects.filter(post=instance), many=True).data,
            'liked': LikedSerializer(Liked.objects.filter(post=instance), many=True).data,
        })
        return Response(post_data)
    
    def destroy(self, request, *args, **kwargs):
        is_user_id_1(request)
        instance = self.get_object()
        if request.user == instance.user:
            instance.delete()
            return Response({"success"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "you can't delete this like"}, status=status.HTTP_400_BAD_REQUEST) 


@extend_schema(tags=['Comment'])
class CommentAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    GenericViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def list(self, request):
        queryset = Comment.objects.all()
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        is_auth(request)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def create(self, request):
        is_auth(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(user=request.user)
        return Response({'success': CommentSerializer(comment).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            instance.delete()
            return Response({"success"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "you can't delete this comment"}, status=status.HTTP_400_BAD_REQUEST) 
    
@extend_schema(tags=['Liked'])
class LikedVAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Liked.objects.all()
    serializer_class = LikedSerializer

    def create(self, request):
        is_auth(request)
        serializer = LikedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_rated = Liked.objects.filter(user_id=self.request.user, post_id=serializer.validated_data['post']).exists()
        if is_rated:
            return Response({"detail": "You can't rate a post more than once."}, status=status.HTTP_400_BAD_REQUEST)
        liked = serializer.save(user=request.user)
        return Response(
            {
                'success': LikedSerializer(liked).data
            }
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user == instance.user:
            instance.delete()
            return Response({"success"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "you can't delete this like"}, status=status.HTTP_400_BAD_REQUEST) 
    
@extend_schema(tags=['Favorite'])
class FavoriteAPIView(AuthenticatedMixin, mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = FavoriteSerializer
        
    def create(self, request):
        serializer = FavoriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        posts = serializer.validated_data['posts']
        user = request.user

        existing_favorites = Favorite.objects.filter(posts__in=posts, user=user)
        if existing_favorites.exists():
            raise Exception('One or more posts are already in your favorites.')
        favorites = serializer.save(user=request.user)
        return Response({
            'success': FavoriteSerializer(favorites).data
        }, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        try:
            return Favorite.objects.filter(user=self.request.user)
        except Favorite.DoesNotExist:
            raise Exception("favorite does not exist")
        except:
            raise Exception("user not authentificated")