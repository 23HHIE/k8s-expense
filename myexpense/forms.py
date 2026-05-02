from django import forms

from .models import Expense, Budget

# a class to describe the expense form
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['type', 'fee', 'payment_date']
        

# a class to describe the budegt form
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount']


# a class to describe the updated budget form 
class UpdateBudgetForm(forms.Form):
    budgetAmount = forms.DecimalField(label='Budget Amount', max_digits=10, decimal_places=2)