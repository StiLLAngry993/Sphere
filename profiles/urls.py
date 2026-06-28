from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("me/", views.profile_view, name="me"),
    path("edit/", views.profile_edit_view, name="edit"),
    path("<str:username>/", views.profile_view, name="view"),
]
