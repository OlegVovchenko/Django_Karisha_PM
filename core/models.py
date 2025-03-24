from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from datetime import timedelta

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

    def check_availability(self):
    # Проверка, что мастер свободен в указанное время
        overlapping_visits = Visit.objects.filter(
            master=self.master,
            status__in=[0, 1],  # Не подтверждена или подтверждена
            appointment_datetime__lt=self.appointment_datetime + timedelta(minutes=self.total_duration()),
            appointment_datetime__gt=self.appointment_datetime - timedelta(minutes=30)  # Буфер между визитами
        ).exclude(pk=self.pk)
        return not overlapping_visits.exists()
    
    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
