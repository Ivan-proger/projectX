import json
import aio_pika
import asyncio
import os
import threading
from django.dispatch import Signal
from django.conf import settings
from asgiref.sync import async_to_sync



# Создаем сигнал для передачи ответа
task_completed = Signal()


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        """Подключение к RabbitMQ, если не подключено."""
        if not self.connection or self.connection.is_closed:
            print("\n [👾] Подключение к RabbitMQ \n")
            self.connection = await aio_pika.connect_robust(
                f"amqp://{os.getenv('RABBITMQ_DEFAULT_USER')}:{os.getenv('RABBITMQ_DEFAULT_PASS')}@rabbitmq/",
            )
            self.channel = await self.connection.channel()
            print(f"[👾] Подключение успешно: {self.connection} \n")

    async def send_task(self, task_data):
        """Отправка задачи в очередь."""
        message = json.dumps(task_data)
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key="task_queue"
        )
        print(" [👾] Задача отправлена:", task_data)



    async def start_consumer(self):
        """Запуск потребителя и прослушивание очереди."""
        await self.connect()
        queue = await self.channel.declare_queue('response_queue', durable=True)
        print("[👾] Начало потребления сообщений...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        print(f"\n [✅] Получено сообщение: {message.body.decode()}")
                        # Логика обработки сообщения здесь
                    except Exception as e:
                        print(f"Ошибка при обработке сообщения: {e}")
                    finally:
                        print("Обработка сообщения завершена.")


    async def continuous_listener(self):
        """Запуск непрерывного прослушивания очереди."""
        await self.connect()
        print("[👾] Фоновый процесс прослушивания очереди запущен...")

        while True:
            try:
                await self.start_consumer()
                print(" -- [👾] Цикл работает епт --")
                # Вы можете настроить время ожидания между итерациями при необходимости
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[❌] Ошибка в фоновом процессе: {e}")
                # Можно добавить логику повторного подключения или обработку ошибок


    async def close(self):
        """Закрытие соединений и каналов."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        print("[👾] Соединение с RabbitMQ закрыто")




# Запуск фонового прослушивателя при старте приложения

# Создаем глобальный экземпляр сервиса
rabbitmq_client = RabbitMQClient()


# Функция для запуска слушателя в отдельном потоке
# def start_listener():
#         print("\n [👾] Запуск \n")
#         loop = asyncio.get_event_loop()
#         rabbitmq_service = RabbitMQClient()
#         print("\n [👾] Запуск работы... \n")
#         # Запуск прослушивания в отдельной задаче
#         loop.create_task(rabbitmq_service.start_consumer())
#         print("\n [👾] Запущен луп... \n")
#         try:
#             # Поддержание работы основного цикла событий
#             loop.run_forever()
#         except KeyboardInterrupt:
#             print("[👾] Завершение работы...")
#             loop.run_until_complete(rabbitmq_service.close())
#             loop.stop()

