from django.contrib import admin

from .models import ImmoscoutUser, ImmoscoutUserData, ApplicationProfile, Flat
from .bot import ImmoscoutBot

class ImmoscoutUserAdmin(admin.ModelAdmin):
    readonly_fields=('user', 'active',)
    
admin.site.register(ImmoscoutUser, ImmoscoutUserAdmin)
admin.site.register(ImmoscoutUserData, ImmoscoutUserAdmin)
admin.site.register(ApplicationProfile)


class ImmoscoutBotAdmin(admin.ModelAdmin):
    readonly_fields=('proxy', 'daemon', 'profile', 'thread', 'telegram', 'app', 'active', 'login_data', 'user_data', 'name')
admin.site.register(ImmoscoutBot, ImmoscoutBotAdmin)

class FlatAdmin(admin.ModelAdmin):
    readonly_fields = ('timestamp',)
admin.site.register(Flat, FlatAdmin)