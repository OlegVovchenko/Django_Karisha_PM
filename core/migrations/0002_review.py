# Generated by Django 5.1.7 on 2025-03-26 14:32

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Имя')),
                ('text', models.TextField(max_length=400, validators=[django.core.validators.MinLengthValidator(30)], verbose_name='Текст')),
                ('rating', models.IntegerField(choices=[(1, 'Ужасно'), (2, 'Плохо'), (3, 'Нормально'), (4, 'Хорошо'), (5, 'Отлично')], verbose_name='Рейтинг')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('status', models.IntegerField(choices=[(0, 'Опубликован'), (1, 'Не проверен'), (2, 'Одобрен'), (3, 'Отклонен')], default=1, verbose_name='Статус')),
                ('master', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.master', verbose_name='Мастер')),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'ordering': ['-created_at'],
            },
        ),
    ]
