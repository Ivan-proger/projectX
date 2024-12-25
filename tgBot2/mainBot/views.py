#import asyncio
import telebot
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .telegram.bot import bot


@csrf_exempt
async def telegram_webhook(request):
    if request.method == 'POST':
        json_str = request.body.decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        await bot.process_new_updates([update])  # Асинхронный вызов
        #asyncio.run(bot.process_new_updates([update])) # Синхронный
        return JsonResponse({"status": "ok"})
    return HttpResponse("Hello! I'm working", status=200)



