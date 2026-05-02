from django.urls import path
from . import views

app_name = 'myexpense'
urlpatterns = [
    # navigate to the landing page
    path('', views.LandingPage.as_view(), name='landing_page'),

    # navigate to the expenses list page
    path('details/', views.expense_list, name='expense_list'),
    
    # navigate to the adding new expense page
    path('add/', views.add_expense, name='add_expense'),

    # navigate to the expense modifying page
    path('modify/<int:expense_id>/', views.modify_expense, name='modify_expense'),
    
    # navigate to the delete expense page
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),

    # navigate to the budget update page
    path('setbudget/<int:user_id>/', views.update_budget, name='update_budget'),

]
