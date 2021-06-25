from django.urls import path

from itou.www.stats import views


app_name = "stats"

urlpatterns = [
    path("", views.public_basic_stats, name="public_basic_stats"),
    path("advanced/", views.public_advanced_stats, name="public_advanced_stats"),
    path("vip/", views.stats_vip, name="stats_vip"),
]
