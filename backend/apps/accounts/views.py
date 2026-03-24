from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

from apps.accounts.forms import RegistrationForm, ProfileForm
from apps.cart.services import merge_anonymous_cart_into_user_cart


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            merge_anonymous_cart_into_user_cart(request, user)

            login(request, user)
            messages.success(request, _('Conta criada com sucesso!'))
            return redirect('catalog:shop_home')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Perfil atualizado com sucesso.'))
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related('items').all()
    return render(request, 'accounts/order_history.html', {'orders': orders})
