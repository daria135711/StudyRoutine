from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'username', 'email')
    list_display_links = ('id_user', 'username')
    search_fields = ('username', 'email')
    ordering = ('id_user',)