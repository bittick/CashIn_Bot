from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp


# def create_long_ikb(data:list, index = 0, size = 6):
#     ikb =  InlineKeyboardMarkup()
#     if index != 0:
#         ikb.add(
#             InlineKeyboardButton('<< назад', callback_data='back')
#         )
#     if index + size > len(data):
#         ikb.add(InlineKeyboardButton('вперед >>', callback_data='forward'))
#     return ikb
    
# # Эхо хендлер, куда летят текстовые сообщения без указанного состояния
# @dp.message_handler(state=None)
# async def bot_echo(message: types.Message):
#     await message.answer(
#         f"{message.text}",
#         reply_markup=create_ikb(['test'],['test'] )
#         )


# # Эхо хендлер, куда летят ВСЕ сообщения с указанным состоянием
# @dp.message_handler(state="*", content_types=types.ContentTypes.ANY)
# async def bot_echo_all(message: types.Message, state: FSMContext):
#     state = await state.get_state()
#     await message.answer(f"Эхо в состоянии <code>{state}</code>.\n"
#                          f"\nСодержание сообщения:\n"
#                          f"<code>{message}</code>")
