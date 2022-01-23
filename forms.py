from django import forms

from .models import ImmoscoutUser, ImmoscoutUserData

class ImmoscoutUserForm(forms.ModelForm):
    username = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput(render_value = True), label='Password')
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['id'] = visible.field.label
            
    class Meta:
        model = ImmoscoutUser
        fields = ('username', 'password')
        
    def save(self, user=None, commit=True):
        user_profile = super(ImmoscoutUserForm, self).save(commit=False)
        if user and not ImmoscoutUser.objects.exists(user=user):
            user_profile.user = user
        if commit:
            user_profile.save()
        return user_profile
        

class ImmoscoutUserDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = visible.field.label
            visible.field.widget.attrs['id'] = visible.field.label
            
    class Meta:
        model = ImmoscoutUserData
        fields = ('gender', 'last_name', 'first_name', 'email', 'phone', 'street', 
                  'house', 'post_code', 'city')
        
    def save(self, profile=None, user=None, commit=True):
        user_profile = super(ImmoscoutUserDataForm, self).save(commit=False)
        if profile:
            user_profile.application_profile = profile
        if user:
            user_profile.user = user
        if commit:
            user_profile.save()
        return user_profile
