import requests
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from loader import dp
from settings import django_url
from keyboards.inline.ikb import courier_kb, dispatcher_kb

@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    req = requests.get(url=django_url + f'user/{message.from_user.id}/')
    if req.status_code == 200:
        data = req.json()
        if data['type'] == 'courier':
            await message.answer(
                f"Привет, {message.from_user.full_name}!\nРоль: курьер\nБаланс: {data['account_balance']}",
                reply_markup=courier_kb,
                )
        elif data['type'] == 'dispatcher':
            await message.answer(
                f"Привет, {message.from_user.full_name}!\nРоль: диспетчер",
                reply_markup=dispatcher_kb,
            )
    else:
        await message.reply('Вы не зарегистрированны!')