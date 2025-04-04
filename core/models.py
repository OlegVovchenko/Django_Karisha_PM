from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MinLengthValidator
from datetime import timedelta
from django.utils.safestring import mark_safe

# Класс для мастеров
class Master(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    
    # Добавлен валидатор для телефона
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Телефон должен быть в формате: '+999999999'. До 15 цифр разрешено."
)

    phone = models.CharField(
        validators=[phone_regex],
        max_length=20, 
        verbose_name='Телефон', 
        db_index=True
    )
    
    address = models.CharField(max_length=255, verbose_name='Домашний адрес')
    photo = models.ImageField(upload_to='masters/photos/', blank=True, null=True, verbose_name='Фотография')
    services = models.ManyToManyField('Service', related_name='masters', verbose_name='Услуги')
    
    # Добавлено поле для отслеживания доступности мастера
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"

# Класс для услуг
class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    
    # Добавлен валидатор для цены
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена',
        validators=[MinValueValidator(0.01, message="Цена должна быть положительной")]
    )
    
    duration = models.PositiveIntegerField(verbose_name='Продолжительность (в минутах)')
    
    # Добавлено поле для изображения услуги
    image = models.ImageField(upload_to='services/images/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


# Класс для записи на прием
class Visit(models.Model):

    STATUS_CHOICES = [
        (0, 'Не подтверждена'),
        (1, 'Подтверждена'),
        (2, 'Отменена'),
        (3, 'Выполнена'),
    ]

    name = models.CharField(max_length=100, verbose_name='Имя')
    
    # Добавлен валидатор для телефона
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',  
        message="Телефон должен быть в формате: '+999999999'. До 15 цифр разрешено."
)
    phone = models.CharField(
        validators=[phone_regex],
        max_length=20, 
        verbose_name='Телефон',
        db_index=True
    )
    
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name='Статус')
    master = models.ForeignKey('Master', on_delete=models.CASCADE, verbose_name='Мастер')
    services = models.ManyToManyField('Service', verbose_name='Услуги')
    appointment_datetime = models.DateTimeField(verbose_name='Дата и время приема')

    def __str__(self):
        return f'{self.name} - {self.phone}'

    def total_price(self):
        return sum(service.price for service in self.services.all())

    def total_duration(self):
        return sum(service.duration for service in self.services.all())

    def formatted_appointment_datetime(self):
        return self.appointment_datetime.strftime('%d.%m.%Y %H:%M')

    def colored_status(self):
        colors = {
            0: '<span style="color: #6c757d;">Не подтверждена</span>',
            1: '<span style="color: #28a745;">Подтверждена</span>',
            2: '<span style="color: #dc3545;">Отменена</span>',
            3: '<span style="color: #007bff;">Выполнена</span>',
        }
        return mark_safe(colors.get(self.status, ''))
    colored_status.short_description = 'Статус'

    def check_availability(self):
        """Проверка, что мастер свободен в указанное время"""
        # Получаем время окончания текущей записи
        end_time = self.appointment_datetime + timedelta(minutes=self.total_duration())
        
        # Ищем пересекающиеся записи
        overlapping_visits = Visit.objects.filter(
            master=self.master,
            status__in=[0, 1],  # Не подтверждена или подтверждена
        ).exclude(pk=self.pk)
        
        for visit in overlapping_visits:
            # Вычисляем время окончания существующей записи
            visit_end_time = visit.appointment_datetime + timedelta(minutes=visit.total_duration())
            
            # Проверяем пересечение интервалов
            # Новая запись начинается до окончания существующей
            # И новая запись заканчивается после начала существующей
            if (self.appointment_datetime < visit_end_time and 
                end_time > visit.appointment_datetime):
                return False
        
        return True

    
    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

class Review(models.Model):
    STATUS_CHOICES = [
        (0, 'Опубликован'),
        (1, 'Не проверен'),
        (2, 'Одобрен'),
        (3, 'Отклонен'),
    ]

    RAITING_CHOICES = [
        (1, 'Ужасно'),
        (2, 'Плохо'),
        (3, 'Нормально'),
        (4, 'Хорошо'),
        (5, 'Отлично'),
    ]

    name = models.CharField(max_length=50, verbose_name='Имя')
    text = models.TextField(max_length=400, verbose_name='Текст', validators=[MinLengthValidator(30)])
    master = models.ForeignKey('Master', on_delete=models.CASCADE, verbose_name='Мастер', null=True, blank=True)
    rating = models.IntegerField(choices=RAITING_CHOICES, verbose_name='Рейтинг')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name='Статус')

    def __str__(self):
        return f'{self.name} - {self.rating}'

    def stars_display(self):
        stars = '★' * self.rating + '☆' * (5 - self.rating)
        return stars
    stars_display.short_description = 'Рейтинг'

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']
