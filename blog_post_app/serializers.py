from rest_framework import serializers, status
from .models import User, Post, Comment, Liked, Favorite
from rest_framework.response import Response

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'password']

    def create(self, validated_data):
        password = validated_data.get('password')
        if len(str(validated_data.get('phone_number', ''))) < 9:
            raise Exception("enter more than 9 characters ")
        user = User.objects.create(
            name=validated_data['name'],
            phone_number=validated_data['phone_number']
        )
        user.set_password(password)
        user.save()
        return user


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'description', 'content', 'image']

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'content', 'created_at', 'user']
    
    def create(self, validated_data):
        post = Post.objects.create(**validated_data)
        post.save()
        return post

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'post', 'content', 'created_at', 'user']

    def create(self, validated_data):
        comment = Comment.objects.create(**validated_data)
        comment.save()
        return comment
    
    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance
    

class LikedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liked
        fields = ['id', 'post', 'grade', 'user']
    
    def create(self, validated_data):
        #! Для валидации данных используется другой метод!!!
        grade = validated_data.get('grade')
        if grade > 10 or grade < 0:
            return Response("enter the correct values from 0 to 10", status=status.HTTP_400_BAD_REQUEST)
        try:
            liked_instance = Liked.objects.get(post=validated_data.get('post'), user=validated_data.get('user'))
            liked_instance.peoples_grade += 1
            liked_instance.save()
            return liked_instance
        except Liked.DoesNotExist:
            validated_data['peoples_grade'] = 1
            return super().create(validated_data)

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'posts', 'user']
    
    def create(self, validated_data):
        posts = validated_data.pop('posts', None)
        favorite = Favorite.objects.create(**validated_data)
        favorite.posts.set(posts)
        return favorite