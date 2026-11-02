from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegistrationForm
from .models import CustomerProfile


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('accounts:profile')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(
        request.POST or None,
        instance=profile,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your contact and delivery details were updated.')
        return redirect('accounts:profile')

    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'customer_profile': profile},
    )
