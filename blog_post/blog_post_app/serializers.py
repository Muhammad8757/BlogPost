from rest_framework import serializers
from .models import User, Post, Comment, Favorite

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
        fields = ['id', 'title', 'content', 'created_at', 'is_favorite']
    
    def create(self, validated_data):
        user = self.context['user']
        category = Post.objects.create(**validated_data, user=user)
        category.save()
        return category

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'post', 'content', 'created_at']

    def create(self, validated_data):
        user = self.context['user']
        category = Comment.objects.create(**validated_data, user=user)
        category.save()
        return category
    
class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'post']
    
    def create(self, validated_data):
        user = self.context['user']
        category = Favorite.objects.create(**validated_data ,user=user)
        category.save()
        return category
    