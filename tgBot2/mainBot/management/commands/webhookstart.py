import asyncio

from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process

from django.core.management.base import BaseCommand

from mainBot.telegram.bot import ensure_webhook
from mainBot.rabbitmq_service import rabbitmq_client


class Command(BaseCommand):
    help = 'Обновление вебхука для телеграмма'

    def handle(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_closed():  # Если цикл закрыт, создаём новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(ensure_webhook())
