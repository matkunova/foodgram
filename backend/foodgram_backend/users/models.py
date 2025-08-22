from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import models

from foodgram_backend.constants import NAME_MAX_LENGTH, EMAIL_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(unique=True,
                              max_length=EMAIL_MAX_LENGTH,
                              blank=False,
                              null=False)
    username = models.CharField(
        unique=True,
        blank=False,
        null=False,
        max_length=NAME_MAX_LENGTH,
        validators=[RegexValidator(r'^[\w.@+-]+\Z')])
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        null=False)
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        null=False)
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')
        ordering = ('-created',)

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на себя.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
