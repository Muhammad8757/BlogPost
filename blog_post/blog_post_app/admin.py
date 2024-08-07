from django.contrib import admin
from .models import Liked, Favorite, Post, User, Comment
models = [User, Post, Comment, Liked, Favorite]
for i in models:
    admin.site.register(i)