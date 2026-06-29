from django.urls import path
from . import views

app_name = "chats"

urlpatterns = [
    path("",                          views.inbox,          name="inbox"),
    path("dm/<str:username>/",        views.start_dm,       name="start_dm"),
    path("room/<int:pk>/",            views.room,           name="room"),
    path("group/create/",             views.create_group,   name="create_group"),
    path("react/<int:msg_id>/",       views.react,          name="react"),
    path("edit/<int:msg_id>/",        views.edit_message,   name="edit_message"),
    path("delete/<int:msg_id>/",      views.delete_message, name="delete_message"),
    path("gif/<int:pk>/",             views.send_gif,       name="send_gif"),
]
