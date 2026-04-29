from django.contrib import admin
from .models import Exam

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'date')   # только существующие поля
    list_display_links = ('id', 'name')
    list_filter = ('date',)                 # difficulty нет, убираем
    search_fields = ('name',)
    ordering = ('-date',)
    
    def get_user_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_user_username.short_description = 'Username'
    get_user_username.admin_order_field = 'user__username'