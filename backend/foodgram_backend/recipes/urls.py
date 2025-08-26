from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'recipes'

router = SimpleRouter()
router.register(r'ingredients', views.IngredientViewSet, basename='ingredient')
router.register(r'tags', views.TagViewSet, basename='tag')

urlpatterns = [
    path('recipes/', views.RecipeViewSet.as_view(
        {'get': 'list', 'post': 'create'}), name='recipe-list'),
    path('recipes/<int:pk>/', views.RecipeViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='recipe-detail'),
    path('recipes/<int:pk>/favorite/', views.RecipeViewSet.as_view({
        'post': 'favorite',
        'delete': 'delete_favorite'
    }), name='recipe-favorite'),
    path('recipes/<int:pk>/shopping_cart/', views.RecipeViewSet.as_view({
        'post': 'shopping_cart',
        'delete': 'delete_shopping_cart'
    }), name='recipe-shopping-cart'),
    path('recipes/<int:pk>/get-link/',
         views.RecipeViewSet.as_view({'get': 'get_link'}),
         name='recipe-get-link'),
    path('recipes/download_shopping_cart/',
         views.DownloadShoppingCartView.as_view(),
         name='download-shopping-cart'),
]

urlpatterns += router.urls
