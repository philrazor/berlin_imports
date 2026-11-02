from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import merge_guest_cart


@receiver(user_logged_in)
def merge_cart_after_login(sender, request, user, **kwargs):
    result = merge_guest_cart(request, user)
    if result['skipped']:
        messages.warning(
            request,
            f'{result["skipped"]} unavailable cart item(s) could not be transferred.',
        )
    if result['adjusted']:
        messages.warning(
            request,
            f'{result["adjusted"]} cart item quantity(ies) were limited to available stock.',
        )
