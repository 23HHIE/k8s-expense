from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


# the expense model in the database
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f"{self.type} - ${self.fee}"

# the budget model in the database
class Budget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # a method to add or delete the budget
    def set_budget(self, amount):
        self.amount = amount
        self.save()

    # a method to calculate the availble budget
    def get_remaining_budget(self):
        # store the current date
        today = now().date()
        # store the first date of the current month
        start_day = today.replace(day=1)
        # calculate the expense starts from the first day
        cost_this_month = Expense.objects.filter(

            user=self.user,
            payment_date__gte=start_day
        ).aggregate(total_expenses=models.Sum('fee'))['total_expenses'] or 0
        # calculate the remaining amount of the budget
        remaining_budget = self.amount - cost_this_month
        return round(remaining_budget, 2)

    # a method to retrieve the perentage of the remaining budget
    def get_remaining_budget_percentage(self):
        # retrieve the available budget amount
        remaining_budget = self.get_remaining_budget()
        # store the percentage by dividing the whole buget amount
        if self.amount != 0:
            percentage = round((remaining_budget / self.amount) * 100, 2)
            return percentage
        else:
            return 0

    def __str__(self):
        return f"{self.user.username} - Budget: {self.amount}"
