import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из ingredients.json'

    def handle(self, *args, **options):
        JSON_FILE_PATH = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.json')

        if not os.path.exists(JSON_FILE_PATH):
            self.stdout.write(
                self.style.ERROR(f'Файл {JSON_FILE_PATH} не найден!')
            )
            return

        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stdout.write(
                    self.style.WARNING(f"Пропущен неполный элемент: {item}")
                )
                continue

            if Ingredient.objects.filter(name=name).exists():
                self.stdout.write(
                    self.style.WARNING(f"Ингредиент '{name}' уже существует.")
                )
                continue

            ingredient = Ingredient.objects.create(
                name=name,
                measurement_unit=measurement_unit
            )
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Добавлен: {name}")
            )

        self.stdout.write(
            self.style.SUCCESS(f'Успешно добавлено {count} ингредиентов.')
        )
