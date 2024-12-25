"""
Основные интсрументы для местоположния пользователей 
их опеределения и добавление в базу обновления базы 
продоставляет инструменты для остального кода бота
"""
from typing import Union, Optional
import asyncio
from geopy.geocoders import Nominatim, GoogleV3, Bing, OpenCage, Yandex
from geopy.exc import GeocoderServiceError
from django.core.cache import cache
from django.conf import settings


async def get_geocoder() -> list:
    """Возвращает список провайдеров для геокодирования."""
    return [
        {"name": "Yandex", "geolocator": Yandex(api_key=settings.YANDEX_API_KEY)},      
        {"name": "OpenCage", "geolocator": OpenCage(api_key=settings.OPENCAGE_API_KEY)},          
        {"name": "Nominatim", "geolocator": Nominatim(user_agent="geo_app")},
    ]

async def extract_city_from_json_Yandex(data: dict) -> str:
    """
    Извлекает название города или, если он не найден, административной области Yandex.
    """
    try:
        # Пробуем найти город в "AddressDetails"
        locality = data.get("metaDataProperty", {}) \
                       .get("GeocoderMetaData", {}) \
                       .get("AddressDetails", {}) \
                       .get("Country", {}) \
                       .get("AdministrativeArea", {}) \
                       .get("SubAdministrativeArea", {}) \
                       .get("Locality", {}) \
                       .get("LocalityName")
        if locality:
            return locality

        # Пробуем найти город в "Components"
        components = data.get("metaDataProperty", {}) \
                         .get("GeocoderMetaData", {}) \
                         .get("Address", {}) \
                         .get("Components", [])
        for component in components:
            if component.get("kind") == "locality":  # Ищем ключ с "locality"
                return component.get("name")

        # Если город не найден, пробуем вернуть AdministrativeAreaName
        region = data.get("metaDataProperty", {}) \
                     .get("GeocoderMetaData", {}) \
                     .get("AddressDetails", {}) \
                     .get("Country", {}) \
                     .get("AdministrativeArea", {}) \
                     .get("AdministrativeAreaName")
        if region:
            return region

        # Если ничего не найдено
        return None
    except Exception as e:
        print(e)
        return None

async def extract_city_or_region_from_OpenCage(data: dict) -> str:
    """
    Извлекает название города или региона из ответа API OpenCage.
    """
    try:
        # Попробуем получить город
        city = data.get("components", {}).get("city")
        if city:
            return city

        # Если город отсутствует, вернем регион
        region = data.get("components", {}).get("state")
        if region:
            return region

        # Если ничего не найдено, возвращаем сообщение
        return None
    except Exception as e:
        print(e)
        return None

async def extract_city_or_region_from_Nominatim(data: dict) -> str:
    """
    Извлекает название города или региона из ответа API Nominatim.
    """
    try:
        # Попробуем получить название города из ключа "name"
        city = data.get("name")
        if city:
            return city

        # Если ключ "name" пуст, попробуем получить город из "address"
        address = data.get("address", {})
        city = address.get("city")
        if city:
            return city

        # Если "city" в адресе отсутствует, попробуем получить другой уровень данных
        region = address.get("state")  # Например, регион
        if region:
            return region

        # Если ключ "address" отсутствует, попробуем извлечь из "display_name"
        display_name = data.get("display_name", "")
        if display_name:
            # Разделяем строку на части и возвращаем первый элемент (обычно это город)
            city_or_region = display_name.split(",")[0].strip()
            return city_or_region

        # Если ничего не найдено, возвращаем сообщение
        return None
    except Exception as e:
        print(e)
        return None

#! Главная функция
async def geocode(
    query: Union[str, tuple], 
    reverse: bool = False, 
    language: str = "ru", 
    retries: int = 1, 
    delay: int = 1,
    cache_timeout: int = 1  # Кэш сек
) -> Optional[dict]:
    """
    Асинхронное геокодирование или обратное геокодирование с поддержкой кэша.
    :param query: Адрес (для геокодирования) или координаты (для обратного геокодирования).
    :param reverse: True, если нужно выполнить обратное геокодирование(поиск по адресу) False -- поиск адреса по координатом.
    :param language: Язык результатов.
    :param retries: Количество попыток.
    :param delay: Задержка между попытками (в секундах).
    :param cache_timeout: Время хранения кэша (в секундах).
    :return: Словарь с результатами или None, если все провайдеры не сработали.
    """
    # Создаем уникальный ключ для кэша
    cache_key = f"geocode:{query}:{language}"

    if reverse:        
        # Проверяем кэш
        cached_result = cache.get(cache_key)
        if cached_result:
            # Результат найден в кэше
            return cached_result

    # Если результата в кэше нет, выполняем запрос
    providers = await get_geocoder()
    for provider in providers:
        for attempt in range(retries):
            try:
                geolocator = provider["geolocator"]
                
                # Выбор метода: геокодирование или обратное геокодирование
                if provider['name'] == 'Yandex':
                    # Яндекс.костыль
                    location = await asyncio.to_thread(
                        geolocator.reverse if reverse else geolocator.geocode,
                        query
                    )   
                else:    
                    location = await asyncio.to_thread(
                        geolocator.reverse if reverse else geolocator.geocode,
                        query,
                        language=language
                    ) 
                if location:
                    # Получаем сырые данные
                    raw_data = location.raw
                    print(f"\n\n{raw_data}\n\n")
                    # Пытаемся извлечь город, населенный пункт или область
                    if provider['name'] == 'Yandex':
                        city = await extract_city_from_json_Yandex(raw_data)

                    elif provider['name'] == 'OpenCage':
                        city = await extract_city_or_region_from_OpenCage(raw_data)
                    else:
                        city = await extract_city_or_region_from_Nominatim(raw_data)
                    
                    if city:
                        result = {
                            "latitude": location.latitude,
                            "longitude": location.longitude,
                            "address": city,
                        }
                        # Сохраняем результат в кэш
                        if reverse:
                            cache.set(cache_key, result, timeout=cache_timeout)
                        return result
                    else:
                        return False
            except GeocoderServiceError as e:
                print(f"Ошибка провайдера {provider['name']}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    print(f"Провайдер {provider['name']} недоступен после {retries} попыток.")
                    break

    # Геокодирование не удалось выполнить ни у одного провайдера
    return None
