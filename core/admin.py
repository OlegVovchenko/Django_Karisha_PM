from django.contrib import admin
from .models import Master, Service, Visit, Review


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'is_active')
    list_filter = ('is_active', 'services')
    search_fields = ('first_name', 'last_name', 'phone')
    filter_horizontal = ('services',)
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'is_active')
        }),
        ('Дополнительная информация', {
            'fields': ('address', 'photo', 'services'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration')
    list_filter = ('price', 'duration')
    search_fields = ('name', 'description')
    list_editable = ('price', 'duration')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'price', 'duration')
        }),
        ('Дополнительная информация', {
            'fields': ('description', 'image'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'master', 'appointment_datetime', 'colored_status', 'status', 'created_at')
    list_filter = ('status', 'master', 'appointment_datetime')
    search_fields = ('name', 'phone', 'comment')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'total_price', 'total_duration')
    filter_horizontal = ('services',)
    date_hierarchy = 'appointment_datetime'
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_completed']
    
    fieldsets = (
        ('Клиент', {
            'fields': ('name', 'phone', 'comment')
        }),
        ('Запись', {
            'fields': ('master', 'services', 'appointment_datetime', 'status')
        }),
        ('Информация', {
            'fields': ('created_at', 'total_price', 'total_duration'),
            'classes': ('collapse',)
        }),
    )
    
    def total_price(self, obj):
        return f"{obj.total_price()} ₽"
    total_price.short_description = "Общая стоимость"
    
    def total_duration(self, obj):
        return f"{obj.total_duration()} мин"
    total_duration.short_description = "Общая продолжительность"

    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=1)
        self.message_user(request, f"{queryset.count()} записей отмечены как подтвержденные")
    mark_as_confirmed.short_description = "Отметить как подтвержденные"

    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=2)
        self.message_user(request, f"{queryset.count()} записей отмечены как отмененные")
    mark_as_cancelled.short_description = "Отметить как отмененные"

    def mark_as_completed(self, request, queryset):
        queryset.update(status=3)
        self.message_user(request, f"{queryset.count()} записей отмечены как выполненные")
    mark_as_completed.short_description = "Отметить как выполненные"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'stars_display', 'master', 'status', 'created_at')
    list_filter = ('rating', 'status', 'master')
    search_fields = ('name', 'text')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    actions = ['publish_reviews', 'reject_reviews']
    
    fieldsets = (
        ('Отзыв', {
            'fields': ('name', 'text', 'rating')
        }),
        ('Статус', {
            'fields': ('master', 'status', 'created_at')
        }),
    )

    def publish_reviews(self, request, queryset):
        queryset.update(status=0)
        self.message_user(request, f"{queryset.count()} отзывов опубликовано")
    publish_reviews.short_description = "Опубликовать выбранные отзывы"

    def reject_reviews(self, request, queryset):
        queryset.update(status=3)
        self.message_user(request, f"{queryset.count()} отзывов отклонено")
    reject_reviews.short_description = "Отклонить выбранные отзывы"