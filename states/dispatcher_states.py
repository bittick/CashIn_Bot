from aiogram.dispatcher.filters.state import StatesGroup, State 

class DispatcherCashin(StatesGroup):
    input_amount = State()
    choose_operator = State()
    choose_card = State()
    confirm = State()

class DispatcherCashOut(StatesGroup):
    input_amount = State()
    confirm = State()