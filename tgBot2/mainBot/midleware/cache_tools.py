from django.core.cache import cache, caches
from django.conf import settings
from mainBot.models import СategoryChannel


#! FSM
async def get_user_state(user_id): # Получить статус
    state = await cache.aget(f"user_state:{user_id}")
    if state:
        return state
    return False
async def set_user_state(user_id, state, time=60*25): # Установить
    if state == None:
        cache.delete(f"user_state:{user_id}")
    else:    
        await cache.aset(f"user_state:{user_id}", state, time)  

#! Кэш категорий
async def category_cache() -> list:
    category_cache = await caches['redis'].aget(f'category_Channel_cache')
    if not category_cache:   # Кэшируем базу 
        category_cache = [user async for user in СategoryChannel.objects.all()]
        await caches['redis'].aset(
            f'category_Channel_cache', 
            category_cache, 
            1 if settings.DEBUG else None
            )
    return category_cache