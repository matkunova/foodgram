from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from foodgram_backend.pagination import CustomPagination

from .models import Follow
from .serializers import SetAvatarSerializer, UserWithRecipesSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()


class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = SetAvatarSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'avatar': serializer.get_avatar_url(request.user)},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserWithRecipesSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return User.objects.filter(
            following__user=self.request.user).prefetch_related('recipes')


class UserSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Follow.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow = Follow.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(
            author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        user = request.user

        follow = Follow.objects.filter(user=user, author=author)
        if not follow.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
