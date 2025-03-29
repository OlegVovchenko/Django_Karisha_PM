from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DecimalField, Q
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from datetime import timedelta
from core.models import Visit, Master, Service, Review

def get_visits_statistics():
    """Получение статистики по визитам"""
    # Общее количество визитов по статусам
    visits_by_status = Visit.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Преобразуем в словарь для удобства
    status_counts = {
        status_dict['status']: status_dict['count'] 
        for status_dict in visits_by_status
    }
    
    # Получаем общее количество визитов
    total_visits = sum(status_counts.values())
    
    # Визиты за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_visits = Visit.objects.filter(created_at__gte=thirty_days_ago).count()
    
    return {
        'total_visits': total_visits,
        'status_counts': status_counts,
        'recent_visits': recent_visits,
    }

def get_revenue_statistics():
    """Получение статистики по доходам"""
    # Общий доход (для всех подтвержденных и выполненных визитов)
    completed_visits = Visit.objects.filter(status__in=[1, 3])  # Подтвержденные и выполненные
    
    # Создаем список всех услуг для каждого визита
    total_revenue = 0
    for visit in completed_visits:
        total_revenue += visit.total_price()
    
    # Доход по месяцам
    # Примечание: это упрощенный подход, для реального проекта нужно использовать 
    # более сложные запросы с аггрегацией
    
    # Доход за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_visits = Visit.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=[1, 3]
    )
    recent_revenue = sum(visit.total_price() for visit in recent_visits)
    
    return {
        'total_revenue': total_revenue,
        'recent_revenue': recent_revenue,
    }

def get_masters_statistics():
    """Получение статистики по мастерам"""
    # Количество визитов по мастерам
    visits_by_master = Visit.objects.values('master__first_name', 'master__last_name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Средний рейтинг мастеров
    master_ratings = Review.objects.values('master__first_name', 'master__last_name').annotate(
        avg_rating=Avg('rating')
    ).order_by('-avg_rating')
    
    return {
        'visits_by_master': visits_by_master,
        'master_ratings': master_ratings,
    }

def get_services_statistics():
    """Получение статистики по услугам"""
    # Популярность услуг (количество раз, когда услуга была заказана)
    popular_services = Service.objects.annotate(
        visit_count=Count('visit')
    ).values('name', 'price', 'visit_count').order_by('-visit_count')
    
    return {
        'popular_services': popular_services,
    }

def get_dashboard_statistics():
    """Получение всей статистики для дашборда"""
    return {
        **get_visits_statistics(),
        **get_revenue_statistics(),
        **get_masters_statistics(),
        **get_services_statistics(),
    }
