from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, Exhibit

class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email',)

class MyUserAdmin(UserAdmin):
    add_form_template = None

    fieldsets = (
        (None, {'fields':('email', 'password')}),
        ('Personal info', {'fields':('username', 'thumbnail', 'self_intro', 'major_category', 'address', 'telephone', 'entrance_fee', 'business_hours', 'holiday')}),
        ('Permissions', {'fields':('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields':('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes':('wide',), 'fields':('email', 'password1', 'password2')}),
    )

    form = MyUserChangeForm
    add_form = MyUserCreationForm
    list_display = ('email', 'username', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(User, MyUserAdmin)
admin.site.register(Exhibit)
