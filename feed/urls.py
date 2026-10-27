from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_feed_view, name='home'),
    path('explore/', views.explore_view, name='explore'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('post/<int:pk>/edit/', views.post_edit_view, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete_view, name='post_delete'),
    path('post/<int:pk>/like/', views.toggle_like_view, name='toggle_like'),
    path('post/<int:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment_view, name='delete_comment'),
]
