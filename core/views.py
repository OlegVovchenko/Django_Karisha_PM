from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Master, Service, Visit
from .form import VisitForm

MENU = [
    {'title': 'Главная', 'url': '/', 'active': True},
    {'title': 'Мастера', 'url': '#masters', 'active': True},
    {'title': 'Услуги', 'url': '#services', 'active': True},
    {'title': 'Портфолио', 'url': '#portfolio', 'active': True},
    # {'title': 'Отзывы', 'url': '#reviews', 'active': True},
    # {'title': 'Оставить отзыв', 'url': '/review/create/', 'active': True},
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
