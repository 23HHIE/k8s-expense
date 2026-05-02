from django.urls import path
from . import views
from django.contrib.auth import views as authentication_view

app_name = 'users'
urlpatterns = [
    # navigate to the signup page
    path('register/', views.register, name='register'),
    # navigate to the login page
    path('login/', authentication_view.LoginView.as_view(template_name='users/login.html'), name='login'),
    # navigate to the logout page
    path('logout/', authentication_view.LogoutView.as_view(next_page='/wisespend/'), name='logout'),
    # navigate to the profile page
    path('profile/', views.profile, name='profile')
]
