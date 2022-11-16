from aiogram.dispatcher.filters.state import StatesGroup, State 

class CourierCashin(StatesGroup):
    input_amount = State()
    choose_operator = State()
    confirm = State()

class CourierCashOut(StatesGroup):
    input_amount = State()
    confirm = State()

