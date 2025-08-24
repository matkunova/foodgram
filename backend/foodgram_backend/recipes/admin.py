from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count
from foodgram_backend.constants import MAX_TIME, MIN_TIME

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, ShortLink, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean_cooking_time(self):
        cooking_time = self.cleaned_data.get('cooking_time')
        if cooking_time is not None and cooking_time < MIN_TIME:
            raise ValidationError(
                f'Время приготовления должно быть не меньше {MIN_TIME} '
                f'минуты.')
        if cooking_time is not None and cooking_time > MAX_TIME:
            raise ValidationError(
                f'Время приготовления должно быть не меньше {MAX_TIME} '
                f'минуты.')
        return cooking_time


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added')
    list_filter = ('added',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'added')
    list_filter = ('added',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_code', 'created')
    search_fields = ('recipe__name', 'short_code')


class IngredientInRecipeInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_ingredients = False
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('ingredient'):
                has_ingredients = True

        if not has_ingredients:
            raise ValidationError('Нужен хотя бы один ингредиент.')


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    formset = IngredientInRecipeInlineFormSet
    extra = 1
    min_num = 1
    validate_min = True
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm

    list_display = ('name', 'author', 'cooking_time',
                    'favorites_count', 'created')
    list_filter = ('tags', 'author', 'created')
    search_fields = ('name', 'author__username', 'author__email')
    filter_horizontal = ('tags',)
    inlines = [IngredientInRecipeInline]
    readonly_fields = ('created',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _favorites_count=Count('favorited_by', distinct=True)
        )

    @admin.display(description='В избранном (раз)')
    def favorites_count(self, obj):
        return obj._favorites_count or 0

    def save_formset(self, request, form, formset, change):
        if formset.model == IngredientInRecipe:
            if not any(f.cleaned_data for f in formset.forms if not (
                    f.cleaned_data.get('DELETE'))):
                raise ValidationError(
                    'Нельзя сохранить рецепт без ингредиентов.')
        super().save_formset(request, form, formset, change)
