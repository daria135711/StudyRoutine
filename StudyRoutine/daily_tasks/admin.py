from django.contrib import admin
from .models import DailyTask

@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    # Новый список отображаемых полей
    list_display = (
        'id', 
        'topic', 
        'scheduled_date', 
        'status', 
        'actual_time_spent',
        'created_at'
    )
    
    # Фильтры по новым полям
    list_filter = ('status', 'scheduled_date', 'created_at')
    
    # Поиск по теме и заметкам
    search_fields = ('topic__title', 'notes')
    
    # Сортировка по умолчанию
    ordering = ('-scheduled_date', 'status')
    
    # Редактируемые прямо в списке поля
    list_editable = ('status', 'actual_time_spent')
    
    # Иерархия по дате (теперь scheduled_date)
    date_hierarchy = 'scheduled_date'
    
    # Поля, которые показываются в форме редактирования
    fieldsets = (
        ('Основное', {
            'fields': ('topic', 'scheduled_date', 'status')
        }),
        ('Выполнение', {
            'fields': ('actual_time_spent', 'notes'),
            'classes': ('wide',)
        }),
        ('Системное', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    # Только для чтения
    readonly_fields = ('created_at',)
    
    # Действия для нескольких записей
    actions = ['mark_as_completed', 'mark_as_in_progress']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = 'Отметить выбранные как "Выполнено"'
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_as_in_progress.short_description = 'Отметить выбранные как "В процессе"'