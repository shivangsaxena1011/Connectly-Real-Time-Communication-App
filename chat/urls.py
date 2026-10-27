from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list_view, name='chat_list'),
    path('start/<str:username>/', views.start_direct_chat_view, name='start_chat'),
    path('start/<str:username>/direct/', views.start_direct_chat_view, name='start_direct_chat'),
    path('<uuid:room_id>/', views.chat_room_view, name='chat_room'),
    path('<uuid:room_id>/upload/', views.upload_attachment_view, name='chat_upload'),
    path('<uuid:room_id>/upload-attachment/', views.upload_attachment_view, name='upload_attachment'),
]
