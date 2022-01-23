from django import template
from immoscout.models import ImmoscoutUser, ImmoscoutUserData
from immoscout.forms import ImmoscoutUserForm, ImmoscoutUserDataForm
register = template.Library()

@register.simple_tag
def is_connected(user):
    return ImmoscoutUser.objects.active(user=user)

@register.simple_tag
def is_registered(user):
    return ImmoscoutUserData.objects.active(user=user)
    
@register.simple_tag
def get_register_form(user):
    return ImmoscoutUserDataForm(instance=ImmoscoutUserData.objects.get_or_none(user=user))

@register.simple_tag
def get_connect_form(user):
    return ImmoscoutUserForm(instance=ImmoscoutUser.objects.get_or_none(user=user))