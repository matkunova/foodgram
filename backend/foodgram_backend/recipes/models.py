import random
import string

from django.conf import settings
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from foodgram_backend.constants import (INGREDIENT_MAX_LENGTH,
                                        MAX_INGREDIENT_AMOUNT,
                                        MEASUREMENT_UNIT_MAX_LENGTH,
                                        MIN_INGREDIENT_AMOUNT,
                                        RECIPE_MAX_LENGTH, TAG_MAX_LENGTH)


def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


class Tag(models.Model):
    name = models.CharField('Название', max_length=TAG_MAX_LENGTH, unique=True)
    slug = models.SlugField(
        'Слаг', max_length=TAG_MAX_LENGTH, unique=True,
        validators=[RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$', message='Недопустимые символы в слаге')]
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=INGREDIENT_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=MEASUREMENT_UNIT_MAX_LENGTH)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_measurement')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=RECIPE_MAX_LENGTH)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Теги')
    cooking_time = models.IntegerField('Время приготовления (мин)')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredient_recipes')
    amount = models.IntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT,
                              'Количество ингредиента не может быть меньше 1'),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                'Количество ингредиента не может быть больше 10000')],
        verbose_name='Количество', help_text='Укажите количество ингредиента'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return (f'{self.amount} '
                f'{self.ingredient.measurement_unit} '
                f'{self.ingredient.name}')


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorited_by')
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_favorite')
        ]
        ordering = ('-added',)

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='shopping_cart')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='in_shopping_cart')
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_shopping_cart')
        ]
        ordering = ('-added',)

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe, on_delete=models.CASCADE, related_name='short_link')
    short_code = models.CharField(
        max_length=10, unique=True, default=generate_short_code)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f's/{self.short_code}'

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
