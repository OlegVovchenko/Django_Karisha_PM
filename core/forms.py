from django import forms
from django.core.validators import RegexValidator
from .models import Master, Service, Visit, Review
import datetime

class VisitForm(forms.ModelForm):
    """Форма для записи на прием в салон красоты"""
    
    # Переопределяем поля для лучшего отображения в форме
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваше имя',
            'id': 'name'
        }),
        label='Ваше имя'
    )
    
    # Используем тот же валидатор, что и в модели
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Телефон должен быть в формате: '+999999999'. До 15 цифр разрешено."
    )
    
    phone = forms.CharField(
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Телефон',
            'id': 'phone'
        }),
        label='Телефон'
    )
    
    # Поле для выбора мастера
    master = forms.ModelChoiceField(
        queryset=Master.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'master'
        }),
        label='Мастер',
        empty_label='Выберите мастера'
    )
    
    # Поле для выбора услуги (множественный выбор)
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'id': 'service',
            'size': '3'  # Показывать 3 опции без прокрутки
        }),
        label='Услуги'
    )
    
    # Поле для даты и времени приема
    appointment_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'id': 'appointment_datetime',
            'type': 'datetime-local'  # HTML5 виджет для даты и времени
        }),
        label='Дата и время приема',
        input_formats=['%Y-%m-%dT%H:%M']  # Формат для HTML5 datetime-local
    )
    
    # Поле для комментария
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Комментарий',
            'id': 'comment',
            'rows': '3'
        }),
        label='Комментарий (необязательно)'
    )
    
    class Meta:
        model = Visit
        fields = ['name', 'phone', 'master', 'services', 'appointment_datetime', 'comment']
    
    def __init__(self, *args, **kwargs):
        super(VisitForm, self).__init__(*args, **kwargs)
        # Устанавливаем минимальную дату для выбора - сегодня
        self.fields['appointment_datetime'].widget.attrs['min'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean_appointment_datetime(self):
        """Проверка, что дата и время приема не в прошлом"""
        appointment_datetime = self.cleaned_data.get('appointment_datetime')
        if appointment_datetime < datetime.datetime.now():
            raise forms.ValidationError("Нельзя выбрать дату и время в прошлом")
        return appointment_datetime
    
    def clean(self):
        """Проверка доступности мастера в выбранное время"""
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        appointment_datetime = cleaned_data.get('appointment_datetime')
        services = cleaned_data.get('services')
        
        if master and appointment_datetime and services:
            # Создаем временный объект Visit для проверки доступности
            temp_visit = Visit(
                master=master,
                appointment_datetime=appointment_datetime
            )
            
            # Сохраняем временно, чтобы можно было использовать M2M поле services
            if self.instance.pk:
                temp_visit.pk = self.instance.pk
            
            # Проверяем доступность мастера
            # Примечание: для корректной работы этого метода нужно временно добавить услуги
            # Это упрощенная версия, в реальном проекте может потребоваться более сложная логика
            total_duration = sum(service.duration for service in services)
            
            # Проверяем, нет ли пересечений с другими записями
            overlapping_visits = Visit.objects.filter(
                master=master,
                status__in=[0, 1],  # Не подтверждена или подтверждена
                appointment_datetime__lt=appointment_datetime + datetime.timedelta(minutes=total_duration),
                appointment_datetime__gt=appointment_datetime - datetime.timedelta(minutes=30)  # Буфер между визитами
            )
            
            if self.instance.pk:
                overlapping_visits = overlapping_visits.exclude(pk=self.instance.pk)
            
            if overlapping_visits.exists():
                raise forms.ValidationError(
                    "Выбранный мастер занят в указанное время. Пожалуйста, выберите другое время или мастера."
                )
        
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'text', 'master', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш отзыв (минимум 30 символов)',
                'rows': 4
            }),
            'master': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            })
        }
