from django.contrib import admin
from .models import AppUser, Review

admin.site.register(AppUser)
admin.site.register(Review)