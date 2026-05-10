from django.contrib import admin
from .models import Exam

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    # Обновлённый список полей
    list_display = (
        'id', 
        'title',                    # вместо name
        'exam_date',                # вместо date
        'difficulty',               # новое поле
        'get_user_username',
        'progress_display',         # кастомное поле для прогресса
        'created_at'
    )
    
    # Ссылки на детали
    list_display_links = ('id', 'title')
    
    # Фильтры по актуальным полям
    list_filter = ('difficulty', 'exam_date', 'created_at')
    
    # Поиск по названию и описанию
    search_fields = ('title', 'description', 'user__username')
    
    # Сортировка по дате экзамена
    ordering = ('exam_date',)
    
    # Редактируемые прямо в списке
    list_editable = ('difficulty',)
    
    # Иерархия по дате
    date_hierarchy = 'exam_date'
    
    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основное', {
            'fields': ('title', 'exam_date', 'difficulty', 'user')
        }),
        ('Описание', {
            'fields': ('description',),
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
    actions = ['mark_as_easy', 'mark_as_medium', 'mark_as_hard']
    
    # Кастомные методы
    def get_user_username(self, obj):
        return obj.user.username if obj.user else '-'
    get_user_username.short_description = 'Пользователь'
    get_user_username.admin_order_field = 'user__username'
    
    def progress_display(self, obj):
        """Отображает прогресс в виде процентной полоски"""
        progress = obj.progress_percent
        return f"{progress}% ({obj.completed_topics}/{obj.total_topics})"
    progress_display.short_description = 'Прогресс'
    progress_display.admin_order_field = 'progress_percent'
    
    def mark_as_easy(self, request, queryset):
        queryset.update(difficulty='easy')
    mark_as_easy.short_description = 'Отметить выбранные как "Лёгкие"'
    
    def mark_as_medium(self, request, queryset):
        queryset.update(difficulty='medium')
    mark_as_medium.short_description = 'Отметить выбранные как "Средние"'
    
    def mark_as_hard(self, request, queryset):
        queryset.update(difficulty='hard')
    mark_as_hard.short_description = 'Отметить выбранные как "Сложные"'