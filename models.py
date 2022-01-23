from django.db import models
from django.conf import settings
from bots.models import Profile
from apps.models import App
from immoscout.utils import contains_date
from django.db.models.signals import post_save, post_delete
from django import forms


# Create your models here.


class ImmoscoutUserManager(models.Manager):
    def active(self, user):
        return self.filter(user=user, active=True).exists()
    
    def exists(self, user):
        return self.filter(user=user).exists()
    
    def get_or_none(self, user):
        qs = self.filter(user=user)
        if qs.count() == 1:
            return qs.first()
        else:
            return None
    
class PasswordField(models.Field):
    def formfield(self, **kwargs):
        kwargs['widget'] = forms.PasswordInput(render_value = True)
        return super().formfield(**kwargs)
    
    def db_type(self, connection):
        return 'char(%s)' % self.max_length
    
class ImmoscoutUser(models.Model):
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    username = models.EmailField(max_length=255)
    password = PasswordField(max_length=255)
    active   = models.BooleanField(default=True)
    
    objects = ImmoscoutUserManager()
    def __str__(self):
        return str(self.username)

    
class ImmoscoutUserDataManager(models.Manager):
    def active(self, user):
        return self.filter(user=user, active=True).exists()
    
    def exists(self, user):
        return self.filter(user=user).exists()
    
    def get_or_none(self, user):
        qs = self.filter(user=user)
        if qs.count() == 1:
            return qs.first()
        else:
            return None
         
GENDER_CHOICES = (
        ('Frau', 'Frau'),
        ('Herr', 'Herr'),
    )
class ImmoscoutUserData(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gender     = models.CharField(max_length=128, choices=GENDER_CHOICES)
    last_name  = models.CharField(max_length=128)
    first_name = models.CharField(max_length=128)
    email      = models.CharField(max_length=128)
    phone      = models.CharField(max_length=32, null=True, blank=True)
    street     = models.CharField(max_length=128)
    house      = models.CharField(max_length=128)
    post_code  = models.CharField(max_length=128)
    city       = models.CharField(max_length=128)
    active     = models.BooleanField(default=True)
    
    
    objects = ImmoscoutUserDataManager()
    def __str__(self):
        return str(self.first_name) + ' ' + str(self.last_name)

    
class ApplicationProfileManager(models.Manager):
    def get_or_none(self, bot):
        qs = self.filter(bot=bot)
        if qs.count() == 1:
            return qs.first()
        else:
            return None
        
class ApplicationProfile(Profile):
    url  = models.CharField(max_length=254)
    text = models.TextField(max_length=1020)
    
    objects = ApplicationProfileManager()
    
    def __str__(self):
        return str(self.title)
    
    def use_login(self, user):
        return ImmoscoutUser.objects.active(user=user)
    
class FlatManager(models.Manager):
    def create(self, user, title, link, user_data, login_data, profile):
        qs = self.filter(user=user, link=link)
        if qs.exists():
            flat = qs.first()
            return None if flat.checked else flat
        
        login_data_active = login_data.active if login_data else False
        login_data = login_data if login_data_active else None
        
        user_data_active = user_data.active if user_data else False
        user_data = user_data if user_data_active else None
        return super(FlatManager, self).create(user=user, link=link, title=title, user_data=user_data, 
                                           login_data=login_data, profile=profile)

KEY_WORDS = ('besichtigung', 'termin', 'uhr', 'frist')
class Flat(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title      = models.CharField(max_length=255)
    link       = models.CharField(max_length=255, unique=True)
    profile    = models.ForeignKey(ApplicationProfile, null=True, blank=True, on_delete=models.SET_NULL)
    login_data = models.ForeignKey(ImmoscoutUser, null=True, blank=True, on_delete=models.SET_NULL)
    user_data  = models.ForeignKey(ImmoscoutUserData, null=True, blank=True, on_delete=models.SET_NULL)
    checked    = models.BooleanField(default=False)
    timestamp  = models.DateTimeField(auto_now=True)
    
    objects = FlatManager()
    
    def __str__(self):
        return self.title

    def do_submit(self):
        if not self.checked:
            self.checked = True
            self.save()
            for word in KEY_WORDS:
                if word in self.title.lower():
                    return False
            return not contains_date(self.title)
        return False
    
    
def immoscout_user_post_save_receiver(sender, instance, *args, **kwargs):
    immo_user_data = ImmoscoutUserData.objects.get_or_none(user=instance.user)
    if immo_user_data:
        if instance.active == immo_user_data.active:
            immo_user_data.active = not instance.active
            immo_user_data.save()
    elif not instance.active:
        instance.active = True
        instance.save()
post_save.connect(immoscout_user_post_save_receiver, sender=ImmoscoutUser)

def immoscout_user_post_delete_receiver(sender, instance, *args, **kwargs):
    immo_user_data = ImmoscoutUserData.objects.get_or_none(user=instance.user)
    if immo_user_data:
        immo_user_data.active = True
        immo_user_data.save()
post_delete.connect(immoscout_user_post_delete_receiver, sender=ImmoscoutUser)

def immoscout_user_data_post_save_receiver(sender, instance, *args, **kwargs):
    immo_user = ImmoscoutUser.objects.get_or_none(user=instance.user)
    if immo_user:
        if instance.active == immo_user.active:
            immo_user.active = not instance.active
            immo_user.save()
    elif not instance.active:
        instance.active = True
        instance.save()
post_save.connect(immoscout_user_data_post_save_receiver, sender=ImmoscoutUserData)

def immoscout_user_data_post_delete_receiver(sender, instance, *args, **kwargs):
    immo_user = ImmoscoutUser.objects.get_or_none(user=instance.user)
    if immo_user:
        immo_user.active = True
        immo_user.save()
post_delete.connect(immoscout_user_data_post_delete_receiver, sender=ImmoscoutUserData)

