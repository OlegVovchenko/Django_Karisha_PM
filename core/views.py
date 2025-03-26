from django.views.generic import TemplateView, CreateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Master, Service, Visit, Review
from .forms import VisitForm, ReviewForm
from django.shortcuts import redirect
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

MENU = [
    {'title': 'Главная', 'url': '/', 'active': True},
    {'title': 'Мастера', 'url': '#masters', 'active': True},
    {'title': 'Услуги', 'url': '#services', 'active': True},
    {'title': 'Портфолио', 'url': '#portfolio', 'active': True},
    {'title': 'Отзывы', 'url': '#reviews', 'active': True},
    {'title': 'Оставить отзыв', 'url': '/review/create/', 'active': True},
    {'title': 'Запись на прием', 'url': '#orderForm', 'active': True},
]

class MainView(CreateView):
    template_name = 'main.html'
    form_class = VisitForm
    success_url = reverse_lazy('thanks')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        context['masters'] = Master.objects.filter(is_active=True)
        context['services'] = Service.objects.all()
        context["reviews"] = Review.objects.filter(status=0).order_by('-created_at')[:6]
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Ваша заявка успешно отправлена!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

class ThanksView(TemplateView):
    template_name = 'thanks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = MENU
        return context

class VisitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Visit
    template_name = 'visit_list.html'
    context_object_name = 'visits'
    paginate_by = 1

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