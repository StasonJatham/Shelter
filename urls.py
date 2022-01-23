from django.urls import path
from django.contrib.auth.views import LogoutView
#from django.views.decorators.csrf import csrf_exempt
from .views import (
    ImmoscoutDataCreateView,
    ImmoscoutCreateView,
    ImmoscoutDeleteView,
    SettingsView,
    ActivateImmoscoutUserView,
    ActivateImmoscoutUserDataView
)

app_name = 'immoscout'
urlpatterns = [
    path('user/create', ImmoscoutCreateView.as_view(), name='user_create'),
    path('user/delete', ImmoscoutDeleteView.as_view(), name='user_delete'),
    path('user/data/create', ImmoscoutDataCreateView.as_view(), name='user_data_create'),
    path('settings', SettingsView.as_view(), name='settings'),
    path('change/connect', ActivateImmoscoutUserView.as_view(), name='connect'),
    path('change/register', ActivateImmoscoutUserDataView.as_view(), name='register'),
]