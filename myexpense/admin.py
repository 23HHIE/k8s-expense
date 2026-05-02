from django.contrib import admin

# Register your models here.
from .models import Expense,Budget
admin.site.register(Expense)
admin.site.register(Budget)