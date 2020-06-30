from django.contrib import admin
from .models import AppUser, Review, Like

admin.site.register(AppUser)
admin.site.register(Review)
admin.site.register(Like)
