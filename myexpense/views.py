from datetime import datetime
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from .models import Expense, Budget
from .forms import ExpenseForm, UpdateBudgetForm
from django.contrib.auth.decorators import login_required

# a simple template view of the landing page
class LandingPage(TemplateView):
    template_name = 'myexpense/landingpage.html'



# set a viriable of the route to avoid duplication
details_page = 'myexpense:expense_list'



# a method to showcase all the expense for the requestd user
@login_required()
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user)
    return render(request, 'myexpense/expenses.html', {'expenses': expenses})


# a method for users to add a new expense
@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect(details_page)
    else:
        form = ExpenseForm()
    return render(request, 'myexpense/addexpense.html', {'form': form})


# a method for users to update an existed expense
@login_required
def modify_expense(request, expense_id):
    # fetch the specific expense
    expense = Expense.objects.get(id=expense_id)
    if request.method == 'POST':
        # fetch all the value of the expense
        expense.type = request.POST.get('type')
        expense.fee = request.POST.get('fee')
        payment_date_str = request.POST.get('payment_date')
        # exchange the date formate
        if payment_date_str:
            expense.date = datetime.strptime(payment_date_str, '%B %d, %Y').date()
        expense.save()
        return redirect(details_page)
    context = {'expense': expense}
    return render(request, 'myexpense/modifyexpense.html', context)
    


# a method for users to delete a specific expense
@login_required
def delete_expense(request, expense_id):
    # fetch the expense requested
    expense = get_object_or_404(Expense, id=expense_id)
    # store the expense to the context
    context = {'expense': expense}
    if request.method == 'POST':
        # execute the in-builte deleted method
        expense.delete()
        return redirect(details_page)
    return render(request, 'myexpense/delete.html', context)

# a method to update a budget
@login_required
@require_POST
def update_budget(request, user_id):
    # fetch the user requested
    user = get_object_or_404(User, id=user_id)
    # retrieve the budget depense on the requested user, or create a new budget if there is none
    budget, _ = Budget.objects.get_or_create(user=user)
    if request.method == 'POST':
        # store the value in the form
        form = UpdateBudgetForm(request.POST)
        if form.is_valid():
            budget_amount = form.cleaned_data['budgetAmount']
            budget.amount = budget_amount
            budget.save()
        # trace the eroor message 
        else:
            print("Form errors:", form.errors)

    return redirect('users:profile')