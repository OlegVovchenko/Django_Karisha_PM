from django.views.generic import TemplateView, CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Master, Service, Visit, Review
from .forms import VisitForm, ReviewForm
from django.shortcuts import redirect
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test


MENU = [
    {'title': 'Главная', 'url': '/', 'active': True},
    {'title': 'Мастера', 'url': '#masters', 'active': True},
    {'title': 'Услуги', 'url': '#services', 'active': True},
    {'title': 'Портфолио', 'url': '#portfolio', 'active': True},
    {'title': 'Отзывы', 'url': '#reviews', 'active': True},
    {'title': 'Оставить отзыв', 'url': '/review/create/', 'active': True},
    {'title': 'Запись на прием', 'url': '#orderForm', 'active': True},
]

@login_required
@user_passes_test(lambda u: u.is_staff)
def update_visit_status(request, visit_id, status):
    """Обновляет статус записи на прием"""
    if request.method == 'POST':
        visit = get_object_or_404(Visit, id=visit_id)
        
        # Проверяем, что статус допустимый
        if status in [0, 1, 2, 3]:
            old_status = visit.get_status_display()
            visit.status = status
            visit.save()
            
            # Добавляем сообщение об успешном обновлении
            messages.success(
                request, 
                f'Статус записи для {visit.name} изменен на "{visit.get_status_display()}"'
            )
        else:
            messages.error(request, 'Недопустимый статус')
    
    # Возвращаемся на страницу со списком записей
    return redirect('visit_list')


class MainView(CreateView):
    template_name = 'main.html'
    form_class = VisitForm
    success_url = reverse_lazy('thanks')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        context['masters'] = Master.objects.filter(is_active=True)

        # Группируем услуги по 3 для карусели
        services = list(Service.objects.all())
        service_groups = [services[i:i+3] for i in range(0, len(services), 3)]
        context['service_groups'] = service_groups
        
        context['services'] = Service.objects.all()
        context["reviews"] = Review.objects.filter(status=0).order_by('-created_at')[:3]
        context['total_reviews'] = Review.objects.filter(status=0).count()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        master_id = self.request.GET.get('master_id')
        if master_id:
            kwargs['master_id'] = master_id
        return kwargs
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # Проверяем доступность мастера перед сохранением
        master = form.cleaned_data.get('master')
        appointment_datetime = form.cleaned_data.get('appointment_datetime')
        services = form.cleaned_data.get('services')
        
        if master and appointment_datetime and services:
            # Создаем временный объект Visit для проверки
            temp_visit = form.save(commit=False)
            
            # Проверяем доступность мастера
            overlapping_visits = Visit.objects.filter(
                master=master,
                status__in=[0, 1],  # Не подтверждена или подтверждена
            )
            
            # Рассчитываем продолжительность выбранных услуг
            total_duration = sum(service.duration for service in services)
            
            # Получаем время окончания новой записи
            end_time = appointment_datetime + timedelta(minutes=total_duration)
            
            # Проверяем пересечение с существующими записями
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
                    
                    # Если есть пересечение, возвращаем ошибку
                    form.add_error(None, f"Мастер {master.first_name} {master.last_name} занят в указанное время.")
                    return self.form_invalid(form)
        
        # Если все проверки пройдены, сохраняем форму
        response = super().form_valid(form)
        
        # Если это AJAX-запрос, возвращаем JSON
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url()
            })
        
        return response


    def form_invalid(self, form):
        """Обработка невалидной формы"""
        # Добавляем сообщения об ошибках только если есть ошибки
        if form.errors:
            # Если есть общие ошибки формы
            if form.non_field_errors():
                for error in form.non_field_errors():
                    if error:  # Проверяем, что сообщение не пустое
                        messages.error(self.request, error)
            # Иначе добавляем ошибки полей
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        if error:  # Проверяем, что сообщение не пустое
                            field_name = form.fields[field].label if field in form.fields else field
                            messages.error(self.request, f"{field_name}: {error}")
        
        # Если это AJAX-запрос, возвращаем JSON с ошибками
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Преобразуем ошибки в более простой формат
            simple_errors = {}
            for field, errors in form.errors.items():
                simple_errors[field] = [str(error) for error in errors]
            
            return JsonResponse({
                'success': False,
                'errors': simple_errors,  # Упрощенный формат ошибок
                'message': form.non_field_errors()[0] if form.non_field_errors() else 'Пожалуйста, исправьте ошибки в форме.'
            })
        
        return super().form_invalid(form)





class ThanksView(TemplateView):
    template_name = 'thanks.html'

    def get(self, request, *args, **kwargs):
        # Очищаем все сообщения при переходе на страницу благодарности
        storage = messages.get_messages(request)
        for message in storage:
            pass  # Просто итерируемся по сообщениям, чтобы очистить их
        storage.used = True
        
        return super().get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        return context

class VisitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Visit
    template_name = 'visit_list.html'
    context_object_name = 'visits'
    # paginate_by = 1

    def test_func(self):
        """Проверяет, имеет ли пользователь права администратора"""
        return self.request.user.is_staff

    def get_queryset(self):
        """Формируем QuerySet с учетом поиска и фильтрации по мастеру"""
        queryset = Visit.objects.all().order_by('-created_at')

        # Получаем параметры из GET-запроса
        search_query = self.request.GET.get('q', '')
        master_id = self.request.GET.get('master', '')

        # Фильтрация по поисковому запросу (имя или телефон)
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query))

        # Фильтрация по мастеру
        if master_id:
            queryset = queryset.filter(master_id=master_id)

        return queryset

    def get_context_data(self, **kwargs):
        """Добавляем в контекст список мастеров и текущие фильтры"""
        context = super().get_context_data(**kwargs)
        context['masters'] = Master.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_master'] = self.request.GET.get('master', '')
        return context

    def dispatch(self, request, *args, **kwargs):
        """Запрещаем доступ не-администраторам"""
        if not request.user.is_staff:
            return redirect('main')  # Перенаправляем на главную
        return super().dispatch(request, *args, **kwargs)

class ReviewCreateView(CreateView):
    template_name = 'review_form.html'
    form_class = ReviewForm
    success_url = '/#reviews'  # Редирект на секцию с отзывами

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        return context

def get_master_services(request):
    """Возвращает список услуг для выбранного мастера в формате JSON"""
    master_id = request.GET.get('master_id')
    if master_id:
        try:
            master = Master.objects.get(id=master_id)
            services = list(master.services.values('id', 'name', 'price', 'duration'))
            return JsonResponse({'services': services})
        except Master.DoesNotExist:
            return JsonResponse({'error': 'Мастер не найден'}, status=404)
    return JsonResponse({'error': 'Не указан ID мастера'}, status=400)

class ReviewListView(ListView):
    model = Review
    template_name = 'review_list.html'
    context_object_name = 'reviews'
    paginate_by = 9  # По 9 отзывов на странице (3 ряда по 3 карточки)
    
    def get_queryset(self):
        return Review.objects.filter(status=0).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        return context
