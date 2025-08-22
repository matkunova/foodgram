from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from djoser import views as djoser_views
from rest_framework.routers import SimpleRouter
from users.views import UserViewSet

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/token/login/',
         djoser_views.TokenCreateView.as_view(), name='login'),
    path('api/auth/token/logout/',
         djoser_views.TokenDestroyView.as_view(), name='logout'),

    path('api/', include('users.urls')),

    path('api/', include(router.urls)),

    path('api/', include('recipes.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
