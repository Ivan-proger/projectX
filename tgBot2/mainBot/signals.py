from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

from mainBot.models import *
from mainBot.rabbitmq_service import task_completed


@receiver([post_save, post_delete], sender=User)
def clear_user_cache(sender, instance, **kwargs):
    """
    Сигнал для обнуления кэша, связанного с моделью User,
    при изменении или удалении записи.
    """
    cache.aset(f'{instance.external_id}-premium', instance.premium, 60*2+1)
    print(f'\n\n {instance.premium} \n\n')


@receiver(task_completed)
def handle_task_completed(sender, response, **kwargs):
    # Обработка ответа
    print("Обработка полученного ответа:", response)
    # Действия с ответом, например, запись в БД или запуск других процессов
    if response.get('status') == 'completed':
        print("Задача успешно выполнена:", response['result'])