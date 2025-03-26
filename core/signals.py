from django.db.models.signals import post_save
from django.dispatch import receiver
from core.utlils import check_review
from .models import Review

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