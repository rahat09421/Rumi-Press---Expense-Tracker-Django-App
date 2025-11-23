from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("create-admin/", views.create_admin, name="create_admin"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
    path("bootstrap-superuser/", views.bootstrap_superuser, name="bootstrap_superuser"),
    path("admin/set-status/", views.admin_set_status, name="admin_set_status"),
]