from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from keyboards.inline.ikb import confirm_kb, create_ikb
from loader import dp, bot
from settings import django_url
from states.courier_stases import CourierCashin, CourierCashOut
from aiogram.utils.exceptions import ChatNotFound
import requests

async def notifiy_dispatchers(text, courier, amount, operator_name=None):
    r = requests.get(django_url + 'dispatcher/').json()
    text_message = f'{text}\nКурьер: {courier}\nСумма: {amount}'
    if operator_name:
        text_message += f'\nОператор: {operator_name}'
    if r:
        for dispatcher in r:
            try:
                await bot.send_message(
                    chat_id=dispatcher['tg_id'],
                    text=text_message
                )
            except ChatNotFound:
                pass

@dp.callback_query_handler(text='cashin', state=None)
async def use_cashin_button_courier(callback_query: types.CallbackQuery, state: FSMContext):
    await CourierCashin.input_amount.set()
    await callback_query.message.answer(text='Введите колическов средств, которые вы хотите зафиксировать')


@dp.message_handler(state=CourierCashin.input_amount)
async def input_amount_courier_cashin(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 0:
            raise ValueError
        elif amount == 0:
            await state.finish()
            await message.answer('Операция отменена')
        else:
            req = requests.get(
                url=django_url + f'user/{message.from_user.id}/')
            if req.status_code == 200:
                account_balance = req.json()['account_balance']
                if account_balance >= amount:
                    operators = requests.get(django_url+'operators/').json()
                    lables = [i['name'] for i in operators]
                    callbacks = [i['id'] for i in operators]
                    ikb = create_ikb(lables, callbacks)
                    msg = await message.answer(text='Выберите оператора', reply_markup=ikb)
                    await state.update_data(msg=msg.message_id, id=msg.chat.id, amount=amount)
                    await CourierCashin.choose_operator.set()
                else:
                    await message.answer('Недостаточно средств на счету')
            else:
                await message.answer(f'Ошибка при отправке запроса на сервер\nкод ошибки: {req.status_code}')
                await state.finish()

    except ValueError:
        await CourierCashin.input_amount.set()
        await message.answer('Значение указанно не верно.\nЕсли вы хотите отменить кэшин введите 0')


@dp.callback_query_handler(lambda c: c.data.startswith('ikb_'), state=CourierCashin.choose_operator)
async def select_operator_cashin(callback_query: types.CallbackQuery, state: FSMContext):
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
                text=f'Операция: кэшин \nОператор: {operator["name"]} \nСумма: {state_data["amount"]}',
                reply_markup=confirm_kb,
            )
            await state.update_data(
                operator=operator['id'],
                operator_name=operator["name"],
            )
            await CourierCashin.confirm.set()
        except Exception as e:
            await callback_query.message.answer(
                text='Ошибка на стороне сервера.\n Операция была отменена'
            )


@dp.callback_query_handler(text='confirm', state=CourierCashin.confirm)
async def confirm_cashin(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    req = requests.post(
        url=django_url+'courier/cashin/',
        json={
            'tg_id': str(data['id']),
            'amount': data['amount'],
            'operator_id': data['operator']
        }

    )
    if req.status_code == 200:
        await notifiy_dispatchers(
            amount=data['amount'],
            courier=callback_query.from_user.full_name,
            operator_name=data['operator_name'],
            text=f'Уведомление\nПроизведена операция: кэшин',
        )

        await bot.edit_message_text(
            chat_id=data['id'],
            message_id=data['msg'],
            text=f'Операция: кэшин\nСумма: {data["amount"]}\nОператор: {data["operator_name"]}\n_________________________\nОперация завершена'
        )
    else:
        await callback_query.message.answer(f'Ошибка при отправке запроса на сервер\nкод ошибки: {req.status_code}')
    await state.finish()


@dp.callback_query_handler(text='cancel', state='*')
async def cansel_cashin(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data:
        await bot.edit_message_text(
            chat_id=data['id'],
            message_id=data['msg'],
            text=f'Операция отменена',
        )
    await state.finish()


@dp.callback_query_handler(text='cashout', state=None)
async def use_cashout_button(callback_query: types.CallbackQuery, state: FSMContext):
    await CourierCashOut.input_amount.set()
    await callback_query.message.answer(text='Введите колическов средств, которые вы хотите зафиксировать')


@dp.message_handler(state=CourierCashOut.input_amount)
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
            await CourierCashOut.confirm.set()

    except ValueError:
        await CourierCashOut.input_amount.set()
        await message.answer('Значение указанно не верно.\nЕсли вы хотите отменить операцию введите 0')


@dp.callback_query_handler(text='confirm', state=CourierCashOut.confirm)
async def confirm_cashout(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    req = requests.post(
        url=django_url+'courier/cashout/',
        json={
            'tg_id': str(data['id']),
            'amount': data['amount'],
        }
    )
    if req.status_code == 200:
        await notifiy_dispatchers(
            amount=data['amount'],
            courier=callback_query.from_user.full_name,
            text=f'Уведомление\nПроизведена операция: забор наличных средств с Garantex',
        )
        await bot.edit_message_text(
            chat_id=data['id'],
            message_id=data['msg'],
            text=f'Забор наличных средств из Gatantex\n{data["amount"]}\n_________________________\nОперация завершена',
        )
    else:
        await callback_query.message.answer(f'Ошибка при отправке запроса на сервер\nкод ошибки: {req.status_code}')
    await state.finish()
