from django.contrib import admin
from .models import DailyTask

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ('id_daily', 'id_user', 'date', 'id_topic', 'done')
    list_filter = ('date', 'done')
    search_fields = ('id_user__username', 'id_topic__title')
    ordering = ('-date',)
    list_editable = ('done',)
    date_hierarchy = 'date'