import asyncio

from celery import shared_task
from mainBot.rabbitmq_service import rabbitmq_client  # Импортируйте ваш RabbitMQ клиент

@shared_task
def check_response_queue():
    """
    Задача для проверки очереди ответов RabbitMQ.
    """
    print("\n [🎆] Задача решила обработаться.... \n")
    # Запустите метод для проверки очереди
    asyncio.run(rabbitmq_client.start_consumer())  # Или любой другой асинхронный метод
