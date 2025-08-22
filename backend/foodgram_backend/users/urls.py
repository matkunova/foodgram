from django.urls import path

from . import views

urlpatterns = [
    path('users/me/avatar/', views.UserAvatarView.as_view(),
         name='user-avatar'),

    path('users/subscriptions/', views.UserSubscriptionsView.as_view(),
         name='user-subscriptions'),

    path('users/<int:id>/subscribe/',
         views.UserSubscribeView.as_view(), name='user-subscribe'),
]
