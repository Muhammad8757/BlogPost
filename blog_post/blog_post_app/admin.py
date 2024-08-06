from django.contrib import admin

from .models import Liked, Favorite, Post, User, Comment

# Register your models here.

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Liked)
admin.site.register(Favorite)