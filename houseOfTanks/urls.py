"""
URL configuration for houseOfTanks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views.combat_views import IndexView
from .views.log_views import LogView
from .views.combat_views import move, stop, shoot, save_websocket_sid

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LogView.as_view()),
    path('combat', IndexView.as_view()),
    # Ajax endpoints
    path('move', move),
    path('stop', stop),
    path('shoot', shoot),
    path('save_websocket_sid', save_websocket_sid),
]
