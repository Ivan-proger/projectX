from django.db import models
from django.contrib.gis.db import models
from django.utils import timezone
from django.conf import settings
from asgiref.sync import sync_to_async
from datetime import timedelta


# Категории канала
class СategoryChannel(models.Model):
    name = models.CharField(max_length=32, verbose_name="Хэштэг")

    # Простой способ определить какие категории близки друг к другу а какие нет
    weight = models.PositiveIntegerField(default=0, verbose_name='Вес')

    class Meta:
        verbose_name = 'Хэштэг'
        verbose_name_plural = 'Хэштэги'

    def __str__(self):
        return f'{self.name}: {self.weight}'

# Юзеры🥰
class User(models.Model):
    external_id = models.PositiveBigIntegerField(verbose_name='ID')
    name = models.CharField(max_length=32, blank=True, null=True, default="")
    
    region = models.CharField(max_length=32, blank=True, null=True, default="", verbose_name="Город")
    # CREATE EXTENSION postgis;
    location = models.PointField(geography=True, blank=True, null=True, verbose_name="Координаты")
    categories = models.ManyToManyField(СategoryChannel, related_name='users')

    premium = models.BooleanField(default=False, verbose_name='Премиум')
    end_premium = models.DateTimeField(null=True, default=None, verbose_name='Конец премиума')

    ref_people = models.PositiveIntegerField(default=0, verbose_name='Приведенно пользователей')
    ref_code = models.CharField(max_length=20, default='error', verbose_name="Код рефералки")
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='Пригласил' )

    is_superuser = models.BooleanField(default=False, verbose_name='Является ли пользователь админом')
    is_subscription = models.BooleanField(default=False, verbose_name='Подписался ли пользователь на каналы-спосноры')
    last_activity = models.DateTimeField(default=timezone.now, verbose_name='Последняя активность')

    is_ban = models.BooleanField(default=False, verbose_name='Забанен')

    # Обновления активности
    @sync_to_async
    def update_last_activity(self):
        current_date = timezone.now()
        # Проверяем, была ли last_activity в прошлом месяце
        if self.last_activity.year == current_date.year:
            if self.last_activity.month == current_date.month - 1 or (self.last_activity.month == 12 and current_date.month == 1):
                pass # Срабатывает если активность произошла в новом месяце по сравнению с прошлым входом

        self.last_activity = current_date
        self.save()

    class Meta:
        verbose_name = 'Юзер_бота'
        verbose_name_plural = 'Юзеры_бота'

    def __str__(self):
        if self.name:
            return f'{self.name} ({str(self.external_id)})'
        else:
            return str(self.external_id)

    
# Каналы    
class Channel(models.Model):
    user = models.ManyToManyField(User, related_name='Владельцы')
    name = models.CharField(max_length=32)
    description = models.CharField(blank=True, max_length=256, default='', verbose_name='Описание')
    poster = models.CharField(max_length=257, blank=True, default='', verbose_name='Изображение')
    external_id = models.BigIntegerField(verbose_name='ID')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    region = models.CharField(max_length=32, blank=True, null=True, default="", verbose_name="Город")
    # CREATE EXTENSION postgis;
    location = models.PointField(geography=True, blank=True, null=True, verbose_name="Координаты")

    categories = models.ManyToManyField(СategoryChannel, related_name='channels')

    folowers = models.PositiveIntegerField(default=0, verbose_name='Фоловеров')
    likes = models.PositiveIntegerField(default=0, verbose_name='Лайки')
    dislikes = models.PositiveIntegerField(default=0, verbose_name='Дизлайки')
    is_work = models.BooleanField(default=True, verbose_name='Доступен')

    boost = models.PositiveIntegerField(default=0, verbose_name='Уровень буста')
    end_boost_time = models.DateTimeField(default=None, blank=True, null=True, verbose_name='Окончания всех бустов')

    class Meta:
        verbose_name = 'Канал'
        verbose_name_plural = 'Каналы'
    
    def __str__(self):
        if self.name:
            return f'{self.name} ({str(self.external_id)})'
        else:
            return f"'{str(self.external_id)}'"

# Категории для жалоб
class СategoryComplaint(models.Model):    
    name = models.CharField(max_length=32, verbose_name="Категория")

    class Meta:
        verbose_name = 'Категория жалобы'
        verbose_name_plural = 'Категория жалоб'

    def __str__(self):
        return f'{self.name}'

# Жалобы
class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Пожаловлся')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='Жалобы')
    category = models.ForeignKey(СategoryComplaint, on_delete=models.CASCADE, related_name='Категория')
    text = models.CharField(max_length=512, verbose_name="Содержание")
    is_viewed = models.BooleanField(default=False, verbose_name="Просмотрено")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'

    def __str__(self):
        return f'Жалобы для {self.channel.name}: {self.text[:20]}'
    


# комментари  под каналами
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Оставил')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='Комментарии')
    text = models.CharField(max_length=512, verbose_name="Содержание")
    is_viewed = models.BooleanField(default=False, verbose_name="Просмотрено")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарии для {self.channel.name}: {self.text[:20]}'

# Рекламные каналы
class SuperChannel(models.Model):
    name = models.CharField(max_length=32)
    external_id = models.IntegerField(verbose_name='ID')
    subscribers_added = models.PositiveIntegerField(verbose_name="Пришло подписчиков", default=0)

    class Meta:
        verbose_name = 'Рекламный каналы'
        verbose_name_plural = 'Рекламные каналы'

# Статистика сервиса
class ServiceUsage(models.Model):
    date = models.DateField(unique=True)
    count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Статистика активности'
        verbose_name_plural = 'Статистика активности'

    def __str__(self):
        return f'Статистика за {self.date}'
    
