from django.urls import path

from itou.www.dashboard import views


# https://docs.djangoproject.com/en/dev/topics/http/urls/#url-namespaces-and-included-urlconfs
app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="index"),
    path("edit_user_info", views.edit_user_info, name="edit_user_info"),
    path("configure_jobs", views.configure_jobs, name="configure_jobs"),
]
