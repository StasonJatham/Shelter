from django.shortcuts import render, redirect, get_object_or_404
from .forms import ImmoscoutUserForm, ImmoscoutUserDataForm
from .models import ImmoscoutUser, ImmoscoutUserData
from django.http import HttpResponse, Http404
from .bot import ImmoscoutBot
from apps.models import App
from bots.models import Bot
from django.views import View
from django.urls import reverse, resolve
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from bots.views import BotCreateView

# Create your views here.

class SettingsView(LoginRequiredMixin, TemplateView):
    login_url = 'control:login'
    template_name = 'immoscout/settings.html'
    
#This view can create and update
class ImmoscoutDataCreateView(LoginRequiredMixin, UpdateView):
    form_class = ImmoscoutUserDataForm
    login_url = 'control:login'
    
    def get_object(self, queryset=None):
        return ImmoscoutUserData.objects.get_or_none(user=self.request.user)
    
    def form_valid(self, form):
        user_data = form.save(commit=False)
        user_data.user = self.request.user
        user_data.save()
        return HttpResponse('success')
   

#This view can create and update
class ImmoscoutCreateView(LoginRequiredMixin, UpdateView):
    form_class = ImmoscoutUserForm
    login_url = 'control:login'
    
    def get_object(self, queryset=None):
        return ImmoscoutUser.objects.get_or_none(user=self.request.user)
    
    def form_valid(self, form):
        user_login = form.save(commit=False)
        user_login.user = self.request.user
        user_login.save()
        return HttpResponse('success')
  

class ImmoscoutDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'immoscout/delete_confirm.html' # <-- default name
    
    def get_object(self, queryset=None):
        user_login = ImmoscoutUser.objects.get_or_none(user=self.request.user)
        if user_login:
            user_data = ImmoscoutUserData.objects.get_or_none(user=self.request.user)
            if user_data:
                user_data.active = True
                user_data.save()
            else:
                [profile.delete() for profile in self.request.user.profile_set.all() if profile.mode != 'telegram_only']
            return user_login
        
        raise Http404('not found')
        
    def get_success_url(self):
        return reverse('immoscout:settings')
    
class ActivateImmoscoutUserView(LoginRequiredMixin, View):
    def get(self, request):
        instance = ImmoscoutUser.objects.get_or_none(user=request.user)
        if instance:
            instance.active = not instance.active
            instance.save()
        return HttpResponse('success')
            
class ActivateImmoscoutUserDataView(LoginRequiredMixin, View):
    def get(self, request):
        instance = ImmoscoutUserData.objects.get_or_none(user=request.user)
        if instance:
            instance.active = not instance.active
            instance.save()
        return HttpResponse('success')

