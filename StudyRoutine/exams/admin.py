from django.contrib import admin
from .models import Exam

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id_exam', 'title', 'date', 'difficulty', 'id_user')
    list_display_links = ('id_exam', 'title')
    list_filter = ('date', 'difficulty')
    search_fields = ('title',)
    ordering = ('-date',)
    
    def get_user_username(self, obj):
        return obj.id_user.username if obj.id_user else '-'
    get_user_username.short_description = 'Username'
    get_user_username.admin_order_field = 'id_user__username'
