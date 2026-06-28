from django.urls import path
from . import views

app_name = "stories"

urlpatterns = [
    path("upload/",                    views.upload_story,  name="upload"),
    path("save/",                      views.save_story,    name="save"),
    path("view/<str:username>/",       views.story_viewer,  name="viewer"),
    path("viewed/<int:story_id>/",     views.mark_viewed,   name="mark_viewed"),
    path("delete/<int:story_id>/",     views.delete_story,  name="delete"),
]
