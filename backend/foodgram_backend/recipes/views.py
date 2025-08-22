from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram_backend.pagination import CustomPagination

from .filters import RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShoppingCart, ShortLink, Tag
from .serializers import (IngredientSerializer, RecipeGetShortLinkSerializer,
                          RecipeListSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, TagSerializer)
from .utils import generate_shopping_list


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related(
        'tags', 'recipe_ingredients__ingredient', 'author'
    ).all()
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    ordering = ('-created',)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeListSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Требуется авторизация.")
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("Недостаточно прав для редактирования.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Недостаточно прав для удаления.")
        instance.delete()

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not cart_item.exists():
            return Response(
                {'errors': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
        serializer = RecipeGetShortLinkSerializer(
            short_link, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DownloadShoppingCartView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        recipes = Recipe.objects.filter(
            in_shopping_cart__user=user
        ).prefetch_related('recipe_ingredients__ingredient')

        if not recipes.exists():
            return Response(
                {'detail': 'Ваш список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_list = generate_shopping_list(recipes)

        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        """Фильтрация по частичному совпадению name"""
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
