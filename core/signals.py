from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from core.utils import check_review
from .models import Review, Visit
from .telegram_bot import send_telegram_message
from karisha_pm.settings import TELEGRAM_BOT_TOKEN, YOUR_PERSONAL_CHAT_ID
import asyncio

@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    if created:
        review = instance
        
        # Получаем текст отзыва
        review_text = review.text

        # Проверяем отзыв
        if check_review(review_text):
            # Если прошли проверку, меняем status на  2
            review.status = 2
        else:
            # Если не прошли проверку, меняем status на  3
            review.status = 3
        review.save()


@receiver(m2m_changed, sender=Visit.services.through)
def send_telegram_notification(sender, instance, action, **kwargs):
    """
    Обработчик сигнала m2m_changed для модели Visit.
    Отправляет уведомление в Telegram при добавлении услуг в запись на прием.
    """
    if action == 'post_add' and kwargs.get('pk_set'):
        # Получаем все услуги
        services = instance.services.all()
        services_list = [f"{service.name} ({service.price} ₽, {service.duration} мин)" for service in services]
        
        # Рассчитываем общую стоимость и продолжительность
        total_price = sum(service.price for service in services)
        total_duration = sum(service.duration for service in services)
        
        # Форматируем дату и время приема
        appointment_time = instance.appointment_datetime.strftime('%d.%m.%Y %H:%M')
        
        # Формируем сообщение
        message = f"""
🔔 *НОВАЯ ЗАПИСЬ В САЛОН КРАСОТЫ "KARISHA_PM"* 🔔

👤 *Клиент:* {instance.name}
📱 *Телефон:* {instance.phone or 'не указан'}
📝 *Комментарий:* {instance.comment or 'не указан'}

🗓️ *Дата и время приема:* {appointment_time}
👩‍💼 *Мастер:* {instance.master.first_name} {instance.master.last_name}

💇‍♀️ *Выбранные услуги:*
"""
        
        # Добавляем список услуг
        for i, service_info in enumerate(services_list, 1):
            message += f"{i}. {service_info}\n"
        
        # Добавляем итоговую информацию
        message += f"""
💰 *Общая стоимость:* {total_price} ₽
⏱️ *Общая продолжительность:* {total_duration} мин

🔗 [Открыть в админ-панели](http://127.0.0.1:8000/admin/core/visit/{instance.id}/change/)
"""
        
        # Отправляем сообщение
        try:
            asyncio.run(send_telegram_message(TELEGRAM_BOT_TOKEN, YOUR_PERSONAL_CHAT_ID, message))
        except Exception as e:
            print(f"Ошибка при отправке сообщения в Telegram: {e}")
