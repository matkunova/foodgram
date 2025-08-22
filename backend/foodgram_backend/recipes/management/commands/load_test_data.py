from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.conf import settings

from recipes.models import Tag, Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart
from users.models import Follow
import os

import base64

User = get_user_model()


class Command(BaseCommand):
    help = 'Загружает тестовые данные в базу'

    def handle(self, *args, **options):
        self.stdout.write('Удаление старых данных...')

        User.objects.exclude(is_superuser=True).delete()
        Tag.objects.all().delete()
        # Ingredient.objects.all().delete()
        Recipe.objects.all().delete()
        Follow.objects.all().delete()
        Favorite.objects.all().delete()
        ShoppingCart.objects.all().delete()

        self.stdout.write('Создание тестовых данных...')

        # === ТЕГИ ===
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
            {'name': 'Вегетарианское', 'slug': 'vegetarian'},
            {'name': 'Десерт', 'slug': 'dessert'},
        ]
        tags = []
        for data in tags_data:
            tag, created = Tag.objects.get_or_create(**data)
            tags.append(tag)
            self.stdout.write(f'✅ Тег: {tag.name}')

        # === ИНГРЕДИЕНТЫ ===

        ingredients_data = [
            {'name': 'Картофель', 'measurement_unit': 'шт'},
            {'name': 'Лук', 'measurement_unit': 'шт'},
            {'name': 'Морковь', 'measurement_unit': 'шт'},
            {'name': 'Яйцо куриное', 'measurement_unit': 'шт'},
            {'name': 'Молоко', 'measurement_unit': 'мл'},
            {'name': 'Соль', 'measurement_unit': 'г'},
            {'name': 'Сахар', 'measurement_unit': 'г'},
            {'name': 'Мука', 'measurement_unit': 'г'},
            {'name': 'Сливочное масло', 'measurement_unit': 'г'},
            {'name': 'Сыр', 'measurement_unit': 'г'},
        ]
        ingredients = []
        for data in ingredients_data:
            ing, created = Ingredient.objects.get_or_create(**data)
            ingredients.append(ing)
            self.stdout.write(
                f'✅ Ингредиент: {ing.name}, {ing.measurement_unit}')

        # === ПОЛЬЗОВАТЕЛИ ===
        users_data = [
            {
                'username': 'ivan',
                'email': 'ivan@example.com',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'password'
            },
            {
                'username': 'anna',
                'email': 'anna@example.com',
                'first_name': 'Анна',
                'last_name': 'Петрова',
                'password': 'password'
            },
            {
                'username': 'admin_admin',
                'email': 'admin_admin@example.com',
                'first_name': 'Админ',
                'last_name': 'Системы',
                'password': 'password',
                'is_staff': True,
                'is_superuser': True
            },
        ]
        users = []
        for data in users_data:
            is_staff = data.pop('is_staff', False)
            is_superuser = data.pop('is_superuser', False)
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults=data
            )
            if created:
                user.set_password(data['password'])
                if is_staff:
                    user.is_staff = True
                if is_superuser:
                    user.is_superuser = True
                user.save()
            users.append(user)
            self.stdout.write(f'✅ Пользователь: {user.username}')

        # === РЕЦЕПТЫ ===
        recipes_data = [
            {
                'author': users[0],
                'name': 'Омлет с молоком',
                'text': 'Смешать яйца и молоко, жарить на сковороде 5 минут.',
                'cooking_time': 10,
                'image_data': 'omlet.jpg',
                'ingredients': [
                    (ingredients[3], 2),  # Яйцо — 2 шт
                    (ingredients[4], 100),  # Молоко — 100 мл
                    (ingredients[5], 1),  # Соль — 1 г
                ],
                'tags': [tags[0], tags[2]],  # Завтрак, Ужин
            },
            {
                'author': users[0],
                'name': 'Картофель по-деревенски',
                'text': 'Нарезать картофель, пожарить с луком и морковью.',
                'cooking_time': 30,
                'image_data': 'potato.jpg',
                'ingredients': [
                    (ingredients[0], 4),  # Картофель — 4 шт
                    (ingredients[1], 1),  # Лук — 1 шт
                    (ingredients[2], 1),  # Морковь — 1 шт
                    (ingredients[8], 30),  # Масло — 30 г
                ],
                'tags': [tags[1]],  # Обед
            },
            {
                'author': users[1],
                'name': 'Сырный пудинг',
                'text': 'Смешать сыр, яйца, муку и сахар, запечь в духовке.',
                'cooking_time': 40,
                'image_data': 'pudding.jpg',
                'ingredients': [
                    (ingredients[9], 200),  # Сыр — 200 г
                    (ingredients[3], 3),  # Яйцо — 3 шт
                    (ingredients[7], 50),  # Мука — 50 г
                    (ingredients[6], 50),  # Сахар — 50 г
                ],
                'tags': [tags[4]],  # Десерт
            },
        ]

        # Создаём изображения
        test_images_dir = os.path.join(settings.MEDIA_ROOT, 'test_images')
        os.makedirs(test_images_dir, exist_ok=True)

        # Простые изображения
        from PIL import Image, ImageDraw

        def create_test_image(filename, color, text):
            img = Image.new('RGB', (300, 200), color=color)
            draw = ImageDraw.Draw(img)
            draw.text((50, 90), text, fill='white')
            img.save(os.path.join(test_images_dir, filename))

        create_test_image('omlet.jpg', 'orange', 'Омлет')
        create_test_image('potato.jpg', 'brown', 'Картофель')
        create_test_image('pudding.jpg', 'yellow', 'Пудинг')

        recipes = []
        for data in recipes_data:
            image_path = os.path.join(test_images_dir, data['image_data'])
            recipe = Recipe.objects.create(
                author=data['author'],
                name=data['name'],
                text=data['text'],
                cooking_time=data['cooking_time']
            )
            recipe.tags.set(data['tags'])

            # Добавляем ингредиенты
            for ingredient, amount in data['ingredients']:
                IngredientInRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount
                )

            # Добавляем изображение
            with open(image_path, 'rb') as img_file:
                recipe.image.save(data['image_data'],
                                  ImageFile(img_file), save=True)

            recipes.append(recipe)
            self.stdout.write(f'✅ Рецепт: {recipe.name}')

        # === ПОДПИСКИ ===
        Follow.objects.create(user=users[1], author=users[0])  # Анна → Иван
        self.stdout.write('✅ Анна подписалась на Ивана')

        # === ИЗБРАННОЕ ===
        # Анна добавила омлет
        Favorite.objects.create(user=users[1], recipe=recipes[0])
        self.stdout.write('✅ Омлет в избранном у Анны')

        # === СПИСОК ПОКУПОК ===
        # Анна добавила картофель
        ShoppingCart.objects.create(user=users[1], recipe=recipes[1])
        self.stdout.write('✅ Картофель в корзине у Анны')

        self.stdout.write(self.style.SUCCESS('✅ Тестовые данные загружены!'))
