
from django.contrib import admin
from django.urls import include, path

from tokens.views import CreateTokensAPI, GetCurrentServingToken, NextTokenAPI

urlpatterns = [
    
    path('create-token/', CreateTokensAPI.as_view(), name='create-token'),
    path('next-token/', NextTokenAPI.as_view(), name='next-token'),
    path('current-token/', GetCurrentServingToken.as_view(), name='current-token'),
]
