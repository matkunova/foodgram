import base64

from django.core.files.base import ContentFile
from foodgram_backend.constants import (MAX_INGREDIENT_AMOUNT,
                                        MIN_INGREDIENT_AMOUNT)
from rest_framework import serializers
from users.serializers import UserSerializer

from .models import Ingredient, IngredientInRecipe, Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url)
        return None


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.in_shopping_cart.filter(user=user).exists()

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.image.url)
        return None


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField())
    )
    tags = serializers.ListField(
        child=serializers.IntegerField()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        if value is None:
            raise serializers.ValidationError(
                'Ингредиенты не могут быть null.')
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент.')

        ingredient_ids = []
        for item in value:
            if 'id' not in item:
                raise serializers.ValidationError(
                    'У ингредиента должно быть поле "id".')
            if 'amount' not in item:
                raise serializers.ValidationError(
                    'У ингредиента должно быть поле "amount".')
            if item['amount'] < MIN_INGREDIENT_AMOUNT:
                raise serializers.ValidationError(
                    f'Количество должно быть не меньше '
                    f'{MIN_INGREDIENT_AMOUNT}.')
            if item['amount'] > MAX_INGREDIENT_AMOUNT:
                raise serializers.ValidationError(
                    f'Количество должно быть не больше '
                    f'{MAX_INGREDIENT_AMOUNT}.')
            ingredient_ids.append(item['id'])

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')

        existing_ids = Ingredient.objects.filter(
            id__in=ingredient_ids).values_list('id', flat=True)
        if len(existing_ids) != len(ingredient_ids):
            missing = set(ingredient_ids) - set(existing_ids)
            raise serializers.ValidationError(
                f'Ингредиенты с id={missing} не существуют.')

        return value

    def validate_tags(self, value):
        if value is None:
            raise serializers.ValidationError('Теги не могут быть null.')
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один тег.')

        tag_ids = []
        for item in value:
            if not isinstance(item, int) or item <= 0:
                raise serializers.ValidationError(
                    (f'Некорректный id тега: {item}. '
                     f'Ожидается положительное число.')
                )
            tag_ids.append(item)

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        existing_ids = Tag.objects.filter(
            id__in=tag_ids).values_list('id', flat=True)
        if len(existing_ids) != len(tag_ids):
            missing = set(tag_ids) - set(existing_ids)
            raise serializers.ValidationError(
                f'Теги с id={missing} не существуют.')

        return tag_ids

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не меньше 1 минуты.')
        return value

    def create_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe, ingredient_id=item['id'], amount=item['amount'])
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                {'ingredients': ['Обязательное поле.']})
        if 'tags' not in validated_data:
            raise serializers.ValidationError({'tags': ['Обязательное поле.']})

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance = super().update(instance, validated_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        if tags_data is not None:
            instance.tags.set(tags_data)

        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeGetShortLinkSerializer(serializers.Serializer):
    short_link = serializers.SerializerMethodField(label='short-link')

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/s/{obj.short_code}')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {
            'short-link': data['short_link']
        }
