from rest_framework import serializers
from .models import User, Post, Comment, Liked, Favorite


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'phone_number', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(
            name=validated_data['name'],
            phone_number=validated_data['phone_number']
        )
        user.set_password(password)
        user.save()
        return user
    

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
        fields = ['id', 'post', 'grade', 'user', 'peoples_grade']
    
    def create(self, validated_data):
        peoples_grade = validated_data.get('peoples_grade', 0)
        if validated_data.get('grade') > 10 or validated_data.get('grade') < 0:
            raise Exception("enter the correct values from 0 to 10")
        liked = Liked.objects.create(**validated_data,peoples_grade=peoples_grade+1)
        liked.save()
        return liked

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'posts', 'user']
    
    def create(self, validated_data):
        posts = validated_data.pop('posts', None)
        favorite = Favorite.objects.create(**validated_data)
        favorite.posts.set(posts)
        return favorite