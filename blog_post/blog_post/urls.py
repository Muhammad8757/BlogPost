from django.contrib import admin
from rest_framework.routers import DefaultRouter
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from blog_post_app.views import FeaturedAPIView, PostAPIView, UserAPIView, CommentAPIView, FavoriteAPIView



router = DefaultRouter()
router.register(r'users', UserAPIView, basename='user')
router.register(r'comments', CommentAPIView, basename='comments')
router.register(r'post', PostAPIView, basename='post')
router.register(r'favorite', FavoriteAPIView, basename='favorite')
router.register(r'featured', FeaturedAPIView, basename='featured')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Путь для Swagger UI
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Путь для Redoc UI
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
