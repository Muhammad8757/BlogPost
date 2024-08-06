from django.contrib import admin

from .models import Favorite, Featured, Post, User, Comment

# Register your models here.

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Favorite)
admin.site.register(Featured)