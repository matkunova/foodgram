def generate_shopping_list(recipes):
    """
    Генерирует текстовый список покупок на основе списка рецептов.
    Агрегирует ингредиенты по названию и единице измерения.
    """
    ingredients = {}

    for recipe in recipes:
        for item in recipe.recipe_ingredients.select_related(
                'ingredient').all():
            ing = item.ingredient
            amount = item.amount
            key = (ing.name, ing.measurement_unit)

            if key in ingredients:
                ingredients[key] += amount
            else:
                ingredients[key] = amount

    lines = ['Список покупок\n', '==============\n\n']

    for (name, unit), total in ingredients.items():
        lines.append(f'{name} — {total} {unit}\n')

    return ''.join(lines)
