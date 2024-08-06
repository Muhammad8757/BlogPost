from rest_framework import serializers
from .models import User, Post, Comment, Favorite, Featured

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
    

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'post', 'grade', 'user', 'peoples_grade']
    
    def create(self, validated_data):
        peoples_grade = validated_data.get('peoples_grade', 0)
        if validated_data.get('grade') > 10 or validated_data.get('grade') < 0:
            raise Exception("enter the correct values from 1 to 10")
        favorite = Favorite.objects.create(**validated_data,peoples_grade=peoples_grade+1)
        favorite.save()
        return favorite

class FeaturedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Featured
        fields = ['id', 'posts', 'user']
    
    def create(self, validated_data):
        posts = validated_data.pop('posts', None)
        featured = Featured.objects.create(**validated_data)
        featured.posts.set(posts)
        return featured