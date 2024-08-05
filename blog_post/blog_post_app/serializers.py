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
        fields = ['id', 'title', 'content', 'created_at']
    
    def create(self, validated_data):
        user = self.context['user']
        post = Post.objects.create(**validated_data, user=user)
        post.save()
        return post

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'post', 'content', 'created_at']

    def create(self, validated_data):
        user = self.context['user']
        comment = Comment.objects.create(**validated_data, user=user)
        comment.save()
        return comment
    

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'post', 'grade', 'peoples_grade']
    
    def create(self, validated_data):
        user = self.context['user']
        peoples_grade = validated_data.get('peoples_grade', 0)
        favorite = Favorite.objects.create(**validated_data ,user=user,peoples_grade=peoples_grade+1)
        favorite.save()
        return favorite

class FeaturedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Featured
        fields = ['id', 'posts', 'user']
    
    def create(self, validated_data):
        user = self.context.get('user')
        validated_data['user'] = user
        posts = validated_data.pop('posts', None)
        featured = Featured.objects.create(**validated_data)
        featured.posts.set(posts)
        return featured