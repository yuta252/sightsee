from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, Exhibit, ExhibitPicture, UserLang

class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('id', 'email', 'password')

class MyUserAdmin(UserAdmin):
    add_form_template = None

    fieldsets = (
        (None, {'fields':('id', 'email', 'password')}),
        ('Personal info', {'fields':('username', 'thumbnail', 'self_intro', 'major_category', 'address', 'telephone', 'entrance_fee', 'business_hours', 'holiday', 'knn_model', 'exhibit_csv')}),
        ('Permissions', {'fields':('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields':('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes':('wide',), 'fields':('id', 'email', 'password1', 'password2')}),
    )

    form = MyUserChangeForm
    add_form = MyUserCreationForm
    list_display = ('id', 'email', 'username', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(User, MyUserAdmin)
admin.site.register(Exhibit)
admin.site.register(ExhibitPicture)
admin.site.register(UserLang)
