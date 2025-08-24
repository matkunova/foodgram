import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from foodgram_backend.constants import BATCH_SIZE
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из ingredients.json'

    def handle(self, *args, **options):
        json_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.json')

        if not os.path.exists(json_file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {json_file_path} не найден!')
            )
            return

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ingredients_to_create = []
        seen_names = set()
        duplicates = 0
        invalid_items = 0

        existing_names = set(Ingredient.objects.values_list('name', flat=True))

        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                invalid_items += 1
                self.stdout.write(
                    self.style.WARNING(f"Пропущен неполный элемент: {item}")
                )
                continue

            if name in seen_names:
                duplicates += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Повторяющийся ингредиент в JSON: {name}")
                )
                continue

            if name in existing_names:
                duplicates += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Ингредиент '{name}' уже существует в базе.")
                )
                continue

            ingredients_to_create.append(
                Ingredient(name=name, measurement_unit=measurement_unit)
            )
            seen_names.add(name)

        if ingredients_to_create:
            Ingredient.objects.bulk_create(
                ingredients_to_create, batch_size=BATCH_SIZE)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно добавлено {len(ingredients_to_create)} '
                    f'ингредиентов.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Нет новых ингредиентов для добавления.')
            )

        if invalid_items:
            self.stdout.write(
                self.style.WARNING(
                    f'Пропущено {invalid_items} '
                    f'элементов из-за отсутствия данных.')
            )
        if duplicates:
            self.stdout.write(
                self.style.WARNING(f'Пропущено {duplicates} дубликатов.')
            )
