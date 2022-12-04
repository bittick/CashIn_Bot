from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline.ikb import confirm_kb, create_ikb
from loader import dp, bot
from settings import django_url
from states.dispatcher_states import DispatcherCashin, DispatcherCashOut
from aiogram.utils.exceptions import ChatNotFound
import requests


async def notifiy_couriers(text, amount, operator_name=None):
    r = requests.get(django_url + 'courier/').json()
    text_message = f'{text}\nСумма:{amount}'
    if operator_name:
        text_message += f'\nОператор: {operator_name}'
    if r:
        for courier in r:
            try:
                await bot.send_message(
                    chat_id=courier['tg_id'],
                    text=text_message
                )
            except ChatNotFound:
                pass


@dp.callback_query_handler(text='dis_operators', state=None)
async def print_operators(callback_query: types.CallbackQuery):
    req = requests.get(django_url+'operators/')
    if req.status_code != 200:
        await callback_query.message.answer(f'Ошибка соединения с серверов\nкод ошибки: {req.status_code}')
    else:
        operators = req.json()
        if operators != []:
            answer_text = 'Cписок операторов:\n\n'
            for i in operators:
                answer_text += f'{i["name"]}\n'
        else:
            answer_text = 'В базе нет операторов'
        await callback_query.message.answer(answer_text)


@dp.callback_query_handler(text='dis_cashin', state=None)
async def use_cashin_button_dispatcher(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Введите колическов средств')
    await DispatcherCashin.input_amount.set()


@dp.message_handler(state=DispatcherCashin.input_amount)
async def input_amount_dispatcher_cashout(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 0:
            raise ValueError
        elif amount == 0:
            await state.finish()
            await message.answer('Операция отменена')
        else:
            operators = requests.get(django_url+'operators/').json()
            print(operators)
            lables = [i['user_name'] for i in operators]
            callbacks = [i['tg_id'] for i in operators]
            ikb = create_ikb(lables, callbacks)
            msg = await message.answer(text='Выберите оператора', reply_markup=ikb)
            await state.update_data(msg=msg.message_id, id=msg.chat.id, amount=amount)
            await DispatcherCashin.choose_operator.set()

    except ValueError:
        await DispatcherCashin.input_amount.set()
        await message.answer('Значение указанно не верно.\nЕсли вы хотите отменить операцию введите 0')


@dp.callback_query_handler(state=DispatcherCashin.choose_operator)
async def input_amount_courier_cashin(call: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    try:
        req = requests.get(url=django_url + f'user/{call.from_user.id}/')
        if req.status_code == 200:
            cards = requests.get(django_url + f'operator/{call.data[4:]}/cards/').json()
            lables = [i['card_number'] for i in cards]
            callbacks = [i['id'] for i in cards]
            ikb = create_ikb(lables, callbacks)
            msg = await call.message.answer(text='Выберите карту оператора', reply_markup=ikb)
            await state.update_data(msg=msg.message_id,
                                    id=msg.chat.id,
                                    amount=state_data['amount'],
                                    operator=call.data[4:],
                                    )
            print(call.data)
            await DispatcherCashin.choose_card.set()
        else:
            await call.message.answer(f'Ошибка при отправке запроса на сервер\nкод ошибки: {req.status_code}')
            await state.finish()

    except ValueError:
        await CourierCashin.input_amount.set()
        await call.message.answer('Значение указанно не верно.\nЕсли вы хотите отменить кэшин введите 0')


@dp.callback_query_handler(lambda c: c.data.startswith('ikb_'), state=DispatcherCashin.choose_card)
async def select_operator_cashin_dispatcher(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    if callback_query.data == 'ikb_cancel':
        await bot.edit_message_text(
            message_id=state_data['msg'],
            chat_id=state_data['id'],
            text='Операция отменена'
        )
        await state.finish()
    else:
        try:
            operator_req = requests.get(
                f'{django_url}operators/{callback_query.data[4:]}/')
            if operator_req.status_code != 200:
                raise Exception(
                    f'req status code: {operator_req.status_code }')
            operator = operator_req.json()
            msg = await bot.edit_message_text(
                message_id=state_data['msg'],
                chat_id=state_data['id'],
                text=f'Операция: кэшин \nОператор: {operator["user_name"]} \nСумма: {state_data["amount"]}',
                reply_markup=confirm_kb,
            )
            await state.update_data(
                operator=operator['tg_id'],
                operator_name=operator["user_name"],
            )
            await DispatcherCashin.confirm.set()
        except Exception as e:
            await callback_query.message.answer(
                text='Ошибка на стороне сервера.\n Операция была отменена'
            )


@dp.callback_query_handler(text='confirm', state=DispatcherCashin.confirm)
async def confirm_cashout_dispatcher(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await notifiy_couriers(
        amount=data['amount'],
        operator_name=data['operator_name'],
        text='Заявка\nОперация: кэшин'
    )
    await bot.edit_message_text(
        chat_id=data['id'],
        message_id=data['msg'],
        text=f'Операция: кэшин\nСумма: {data["amount"]}\nОператор: {data["operator_name"]}\n_________________________\nЗаявка отправлена курьерам.',
    )
    await state.finish()


@dp.callback_query_handler(text='dis_cashout', state=None)
async def use_cashout_button_dispatcher(callback_query: types.CallbackQuery, state: FSMContext):
    await DispatcherCashOut.input_amount.set()
    await callback_query.message.answer(text='Введите количество средств, которое будет указано в заявке')


@dp.message_handler(state=DispatcherCashOut.input_amount)
async def input_amount_courier_cashout(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 0:
            raise ValueError
        elif amount == 0:
            await state.finish()
            await message.answer('Операция отменена')
        else:
            msg = await message.answer(
                text=f'Подтверждение операции:\n\nЗабор наличных стредств из Garantex\n{amount}',
                reply_markup=confirm_kb
            )
            await state.update_data(amount=amount, msg=msg.message_id, id=msg.chat.id)
            await DispatcherCashOut.confirm.set()

    except ValueError:
        await DispatcherCashOut.input_amount.set()
        await message.answer('Значение указанно не верно.\nЕсли вы хотите отменить операцию введите 0')


@dp.callback_query_handler(text='confirm', state=DispatcherCashOut.confirm)
async def confirm_cashout(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await notifiy_couriers(
        amount=data['amount'],
        text='Заявка\nОперация: забор наличных средств с Garantex'
        )
    await bot.edit_message_text(
        chat_id=data['id'],
        message_id=data['msg'],
        text=f'Заявка о заборе наличных средств из Gatantex\n{data["amount"]}\n_________________________\nЗаявка отправлена курьерам.',
    )
    await state.finish()

