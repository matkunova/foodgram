from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import base64
import uuid
from .models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        if obj.avatar and hasattr(self, 'context') and self.context.get(
                'request'):
            request = self.context['request']
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class SetAvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField(write_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    def validate_avatar(self, value):
        if not value.startswith('data:image'):
            raise serializers.ValidationError(
                'Некорректный формат изображения.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        avatar_data = self.validated_data['avatar']

        if user.avatar:
            user.avatar.delete(save=False)

        format, imgstr = avatar_data.split(';base64,')
        ext = format.split('/')[-1]
        filename = f'{uuid.uuid4()}.{ext}'

        user.avatar.save(
            filename,
            ContentFile(base64.b64decode(imgstr)),
            save=True
        )
        return user

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request is None:
            return []

        recipes_limit = request.query_params.get('recipes_limit')
        try:
            limit = int(recipes_limit) if recipes_limit else None
        except (TypeError, ValueError):
            limit = None

        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:limit]
        from recipes.serializers import RecipeShortSerializer
        return RecipeShortSerializer(recipes, many=True,
                                     context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
