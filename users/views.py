from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth.decorators import login_required


# a method to handle the register request
def register(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, 'New account has been created for {}!'.format(username))
            return redirect('myexpense:landing_page')
        else:
            print(form.errors)
    elif request.method == 'GET':
        form = NewUserForm()
    context = {
        'form': form,
    }
    return render(request, 'users/register.html', context)


# a method to handle the profile page request
@login_required
def profile(request):
    return render(request, 'users/profile.html')
