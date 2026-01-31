from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    choosing_lang = State()
    entering_code = State() # User activation code or Admin code

class AdminStates(StatesGroup):
    main = State()
    waiting_for_user_code = State() # Amount/Duration for new code?
    waiting_for_setting_value = State() # Generic state for updating settings

class AdCreationStates(StatesGroup):
    managing_draft = State()
    title = State()
    photos = State()
    description = State()
    price = State()
    phone = State()
    confirm = State()
