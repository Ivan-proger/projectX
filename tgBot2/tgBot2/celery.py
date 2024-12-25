import os
from celery import Celery


# Укажите настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tgBot2.settings')

app = Celery('tgBot2')

app.conf.broker_connection_retry_on_startup = True

# Настройка конфигурации
app.config_from_object('django.conf:settings', namespace='CELERY')

#app.conf.broker_url = url

# Автоматическое обнаружение задач в приложениях
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')