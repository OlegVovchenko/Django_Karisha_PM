from django import forms
from django.core.validators import RegexValidator
from .models import Master, Service, Visit, Review
import datetime
from datetime import timedelta

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
            'size': '3',  # Показывать 3 опции без прокрутки
            'style': 'padding-left: 15px; text-indent: 40px;'  # Добавляем отступ слева
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
        master_id = kwargs.pop('master_id', None)
        super(VisitForm, self).__init__(*args, **kwargs)
        
        # Устанавливаем минимальную дату для выбора - сегодня
        self.fields['appointment_datetime'].widget.attrs['min'] = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
        
        # Если выбран мастер, фильтруем услуги
        if master_id:
            master = Master.objects.get(id=master_id)
            self.fields['services'].queryset = master.services.all()
    
    def clean_appointment_datetime(self):
        """Проверка, что дата и время приема не в прошлом"""
        appointment_datetime = self.cleaned_data.get('appointment_datetime')
        
        # Получаем текущее время в том же формате (naive или aware)
        from django.utils import timezone
        now = timezone.now()
        
        # Если appointment_datetime наивное (без часового пояса)
        if timezone.is_naive(appointment_datetime) and not timezone.is_naive(now):
            # Делаем now наивным
            now = timezone.make_naive(now)
        # Если appointment_datetime осведомленное (с часовым поясом)
        elif not timezone.is_naive(appointment_datetime) and timezone.is_naive(now):
            # Делаем now осведомленным
            now = timezone.make_aware(now)
        
        if appointment_datetime < now:
            raise forms.ValidationError("Нельзя выбрать дату и время в прошлом")
        
        return appointment_datetime

    
    def clean(self):
        """Проверка доступности мастера в выбранное время"""
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        appointment_datetime = cleaned_data.get('appointment_datetime')
        services = cleaned_data.get('services')
        
        if master and appointment_datetime and services:
            # Рассчитываем продолжительность выбранных услуг
            total_duration = sum(service.duration for service in services)
            
            # Получаем время окончания новой записи
            end_time = appointment_datetime + timedelta(minutes=total_duration)
            
            # Ищем пересекающиеся записи
            overlapping_visits = Visit.objects.filter(
                master=master,
                status__in=[0, 1],  # Не подтверждена или подтверждена
            )
            
            if self.instance.pk:
                overlapping_visits = overlapping_visits.exclude(pk=self.instance.pk)
            
            # Проверяем каждую существующую запись на пересечение
            for visit in overlapping_visits:
                # Получаем услуги для этой записи
                visit_services = visit.services.all()
                
                # Рассчитываем продолжительность
                visit_duration = sum(service.duration for service in visit_services)
                
                # Вычисляем время окончания существующей записи
                visit_end_time = visit.appointment_datetime + timedelta(minutes=visit_duration)
                
                # Проверяем пересечение интервалов
                if (appointment_datetime < visit_end_time and 
                    end_time > visit.appointment_datetime):
                    
                    # Форматируем время для сообщения
                    visit_start_time = visit.appointment_datetime.strftime('%H:%M')
                    visit_end_time_str = visit_end_time.strftime('%H:%M')
                    
                    # Находим ближайшее свободное время после текущей записи
                    next_available_time = visit_end_time + timedelta(minutes=15)  # Добавляем 15 минут буфера
                    next_available_time_str = next_available_time.strftime('%H:%M')
                    next_available_date_str = next_available_time.strftime('%d.%m.%Y')
                    
                    # Формируем информативное сообщение об ошибке
                    error_message = (
                        f"Мастер {master.first_name} {master.last_name} занят в указанное время "
                        f"(с {visit_start_time} до {visit_end_time_str}). "
                        f"Ближайшее доступное время для записи к этому мастеру: "
                        f"{next_available_date_str} в {next_available_time_str}. "
                        f"Пожалуйста, выберите другое время или другого мастера."
                    )
                    
                    raise forms.ValidationError(error_message)
            
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

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        # Делаем поле master необязательным
        self.fields['master'].required = False
        self.fields['master'].empty_label = "Общий отзыв о салоне"
