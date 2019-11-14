from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm

from .models import User, Exhibit, UserLang


# Exhibit upload form
class ExhibitForm(forms.ModelForm):
    class Meta:
        model = Exhibit
        fields = ('exhibit_name', 'exhibit_desc', 'post_pic', 'exhibit_name_en', 'exhibit_desc_en', 'exhibit_name_zh', 'exhibit_desc_zh')
        widgets = {
            'exhibit_name':forms.TextInput(attrs={'id':'obj_name', 'class':'form-control', 'placeholder':'名称を入力'}),
            'exhibit_desc':forms.Textarea(attrs={'id':'obj_description', 'class':'form-control', 'rows':'5'}),
            'exhibit_name_en':forms.TextInput(attrs={'id':'obj_name', 'class':'form-control', 'placeholder':'名称を入力'}),
            'exhibit_desc_en':forms.Textarea(attrs={'id':'obj_description', 'class':'form-control', 'rows':'5'}),
            'exhibit_name_zh':forms.TextInput(attrs={'id':'obj_name', 'class':'form-control', 'placeholder':'名称を入力'}),
            'exhibit_desc_zh':forms.Textarea(attrs={'id':'obj_description', 'class':'form-control', 'rows':'5'}),
        }

    # To Do : フォームの is_valid()処理を記述
    # def is_valid():

# Contact from
class ContactForm(forms.Form):
    contact_title = forms.CharField(
        label = 'お問い合わせ件名',
        max_length= 255,
        required=True,
        widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'件名を入力'})
    )

    contact_content = forms.CharField(
        label = 'お問い合わせ内容',
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={'class':'form-control', 'placeholder':'お問い合わせ内容を入力'})
    )


# Singup
class SignupForm(UserCreationForm):
    """User registration"""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'thumbnail', 'self_intro')
        widgets = {
            'username': forms.TextInput(attrs={'class':'username-create-form'}),
            'email': forms.EmailInput(attrs={'class':'email-create-form'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        # If manipulation stops in temp registration, remove temp data in the case of re-register
        User.objects.filter(email=email, is_active=False).delete()
        return email

# User edit form
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'thumbnail', 'self_intro', 'major_category', 'address', 'telephone', 'entrance_fee', 'business_hours', 'holiday')
        widgets = {
            'username':forms.TextInput(attrs={'class':'obj_username', 'placeholder':'名称を入力'}),
            'self_intro':forms.Textarea(attrs={'class':'obj_self_intro', 'rows':'7'}),
            # 'post_pic':forms.ImageField(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserLangEditForm(forms.ModelForm):
    class Meta:
        model = UserLang
        fields = ('language', 'username', 'self_intro', 'major_category', 'address', 'entrance_fee', 'business_hours', 'holiday')
        widgets = {
            'language':forms.Select(attrs={'id':'userlang_laguage'}),
            'username':forms.TextInput(attrs={'id':'userlang_username', 'placeholder':'名称を入力'}),
            'self_intro':forms.Textarea(attrs={'id':'userlang_self_intro', 'rows':'7'}),
            'major_category':forms.Select(attrs={'id':'userlang_major_category'}),
            'address':forms.TextInput(attrs={'id':'userlang_address'}),
            'entrance_fee':forms.TextInput(attrs={'id':'userlang_entrance_fee'}),
            'business_hours':forms.TextInput(attrs={'id':'userlang_business_hours'}),
            'holiday':forms.TextInput(attrs={'id':'userlang_holiday'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class MyPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email

# Login form
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label