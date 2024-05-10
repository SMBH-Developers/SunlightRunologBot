import asyncio
import logging
import re

import texts

from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram import executor, types, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import markdown

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from keyboards import Markups
from bf_texts import bf_sending, SendingData
from src.common import settings
from src.models import db, db_sendings
from src import DATA_DIR

from data.skip_100_lead import skip_100_leads


class States(StatesGroup):
    search_rune_by_name = State()
    name = State()
    bth = State()


storage = RedisStorage2(db=settings.redis_db, pool_size=40)
bot = Bot(settings.tg_token)
dp = Dispatcher(bot, storage=storage)
ADMIN_IDS = (1188441997, 791363343)
markups = Markups()

language = 'ru_RU'


async def get_photo_id(path: Path) -> str | types.InputFile:
    photo_id = await db.get_photo_id(path)
    if photo_id is None:
        photo_id = types.InputFile(path)
    return photo_id


@dp.message_handler(commands=['start'], state='*')
@logger.catch
async def start_mes(message: types.Message, state: FSMContext) -> None:
    path = DATA_DIR / 'photos_to_message/start_photo.png'
    photo = await get_photo_id(path)
    await state.finish()
    await db.registrate_if_not_exists(message.from_user.id)
    await message.answer_photo(photo=photo, caption=texts.welcome_text, reply_markup=markups.mrkup_to_start, parse_mode='html')


@dp.message_handler(lambda message: message.from_user.id in ADMIN_IDS, state='*', commands=['admin'])
@logger.catch
async def admin_menu(message: types.Message, state: FSMContext) -> None:
    await bot.send_message(message.chat.id, text='Выберите действие', reply_markup=markups.admin_mrkup)


@dp.callback_query_handler(lambda call: call.from_user.id in ADMIN_IDS and call.data.startswith('Admin'), state='*')
@logger.catch
async def admin_calls(call: types.CallbackQuery, state: FSMContext) -> None:
    action = '_'.join(call.data.split('_')[1:])
    if action == 'Users_Total':
        await call.message.edit_text(text=f'Пользователей всего: {await db.get_count_all_users()}',
                                     reply_markup=markups.back_admin_mrkup)

    elif action == 'Users_For_TODAY':
        await call.message.edit_text(text=f'Пользователей за сегодня: {await db.users_for_today()}',
                                     reply_markup=markups.back_admin_mrkup)

    elif action == 'BACK':
        await call.message.edit_text(text='Выберите действие', reply_markup=markups.admin_mrkup)


@dp.message_handler(lambda message: message.text in markups.titles_mrkup_to_start, state='*')
@logger.catch
async def send_combinations_to_user(message: types.Message, state: FSMContext):
    """При нажатии на кнопку Начать"""
    asyncio.create_task(send_combinations(message.from_user.id))


@logger.catch
async def send_combinations(user_id: int):
    """Отправка комбинаций"""
    await bot.send_message(user_id, texts.text_before_sending_combinations, reply_markup=types.ReplyKeyboardRemove())

    for index, combination in enumerate(texts.combinations):
        photo_id = await get_photo_id(combination['photo'])
        await asyncio.sleep(2)
        msg = await bot.send_photo(user_id, photo_id, caption=combination['text'], reply_markup=types.ReplyKeyboardRemove())
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(combination['photo'], msg["photo"][0]["file_id"])

    await asyncio.sleep(1)
    await bot.send_message(user_id, text=texts.to_send_after_combinations, reply_markup=markups.combinations_mrkup)


@dp.message_handler(lambda message: message.text in markups.titles_of_combination_mrkup, state='*')
@logger.catch
async def answer_on_combination(message: types.Message):
    number = int(message.text[-1])-1
    await db.set_user_chose_combination(message.from_user.id, number)
    await message.answer(texts.analyzes_of_chosen_combination[number], reply_markup=markups.menu_mrkup)
    await asyncio.create_task(send_byte_message(message.from_user.id))


async def send_byte_message(user_id: int):
    await asyncio.sleep(2)
    await bot.send_message(user_id, texts.get_free_analyze, reply_markup=markups.to_our_autoanswer_mrkup)


@dp.message_handler(lambda message: message.text == '👈Обратно', state='*')
@logger.catch
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await message.answer(texts.menu_text, reply_markup=markups.menu_mrkup)


@dp.message_handler(lambda message: message.text == '👈Назад', state='*')
@dp.message_handler(lambda message: message.text == '🧿Все о рунах', state='*')
async def all_about_runes(message: types.Message, state: FSMContext):
    await message.answer(texts.info_menu_text, reply_markup=markups.all_about_runes_mrkup)


@dp.message_handler(lambda message: message.text == 'ℹ️Расшифровка всех рун', state='*')
@logger.catch
async def info_about_runes(message: types.Message, state: FSMContext):
    await message.answer('Выберите руну:', reply_markup=markups.page_mrkups[0])


@dp.message_handler(lambda message: message.text == '📚Обучение руническому раскладу', state='*')
async def study_rune_info_start(message: types.Message, state: FSMContext):
    path = DATA_DIR / "photos_to_message/learning_rune.JPG"
    photo_id = await get_photo_id(path)
    msg = await message.answer_photo(photo_id, texts.study_rune_text_1, reply_markup=markups.study_rune_mrkup_on_page_1)
    if isinstance(photo_id, types.InputFile):
        await db.register_photo(path, msg["photo"][0]["file_id"])


@dp.message_handler(lambda message: message.text == '🤩Получить бесплатный расклад🤩', state='*')
async def menu_metaphorical_analysis(message: types.Message, state: FSMContext):
    await message.answer("Отлично! Для начала, напиши пожалуйста свое Имя 👇", reply_markup=markups.back_to_main_menu_mrkup)
    await state.set_state(States.name.state)


@dp.message_handler(state=States.name)
async def set_number_metaphorical_analysis(message: types.Message, state:FSMContext):
    await message.answer("Супер! День твоего рождения в формате ДД.ММ.ГГГГ 👇", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(States.bth.state)

@dp.message_handler(state=States.bth)
async def menu_metaphorical_analysis(message: types.Message, state: FSMContext):
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'  # Паттерн для формата ДД.ММ.ГГГГ
    if re.match(date_pattern, message.text):
        await message.answer('🥳 Я Вас поздравляю! Вы успели попасть в число счастливчиков на получение бесплатного рунического расклада.\n\n'
                             'Напишите пожалуйста мне в личные сообщения 👉 @RunologyMentor слово "Расклад"', reply_markup=markups.back_to_main_menu_mrkup)
        await state.finish()
    else:
        await message.answer("Ошибка! Введите дату в формате ДД.ММ.ГГГГ")


async def try_del(call: types.CallbackQuery | types.Message):
    try:
        if isinstance(call, types.CallbackQuery):
            await call.message.delete()
        else:
            msg = call
            await msg.delete()
    except:
        ...


@dp.callback_query_handler(lambda call: call.data == 'rune_study_to_page_2', state='*')
@logger.catch
async def study_rune_page_2(call: types.CallbackQuery, state: FSMContext):
    await try_del(call)
    await call.message.answer(texts.study_rune_text_2, reply_markup=markups.study_rune_mrkup_on_page_2)


@dp.callback_query_handler(lambda call: call.data == 'studies_options', state='*')
@logger.catch
async def studies_options(call: types.CallbackQuery, state: FSMContext):
    await try_del(call)
    await call.message.answer(texts.choose_study_rune_option_text, reply_markup=markups.options_studies_rune_mrkup)


@dp.callback_query_handler(lambda call: call.data == 'DELETE', state='*')
async def del_msg(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except exceptions.TelegramAPIError:
        await call.answer('Сообщение устарело, поэтому не может быть удалено.')


@dp.callback_query_handler(lambda call: call.data.startswith('check_study?'), state='*')
async def check_study_of_runes(call: types.CallbackQuery, state: FSMContext):
    key_arg, arg_value = call.data.split('?')[1].split('=')
    arg_value = int(arg_value)
    info_study = texts.studies_rune[arg_value]
    await try_del(call)

    if info_study['photo'] is not None:
        photo_id = await get_photo_id(info_study['photo'])
        msg = await call.message.answer_photo(photo_id, caption=info_study['text'], reply_markup=markups.mrkup_under_every_study_rune)
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(info_study['photo'], msg["photo"][0]["file_id"])

    else:
        await bot.send_message(call.from_user.id, info_study['text'], reply_markup=markups.mrkup_under_every_study_rune)


@dp.callback_query_handler(lambda call: call.data.startswith('info_runes?'), state='*')
async def info_runes(call: types.CallbackQuery, state: FSMContext):
    key_arg, arg_value = call.data.split('?')[1].split('=')
    if key_arg == 'choose_rune':
        index_rune = int(arg_value)
        rune = texts.values_info_runes[index_rune]
        photo_id = await get_photo_id(rune['photo'])
        msg = await call.message.answer_photo(photo_id, caption=rune['text'], reply_markup=markups.mrkup_to_del)
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(rune['photo'], msg["photo"][0]["file_id"])

    elif key_arg == 'next_page':
        index_page = int(arg_value)
        await call.message.edit_text('Выберите руну:', reply_markup=markups.page_mrkups[index_page])

    elif key_arg == 'search_by_name':
        await call.message.edit_text('Введите название руны для поиска 🔎:', reply_markup=markups.cancel_searching_rune_by_name)
        await state.set_state(States.search_rune_by_name.state)

    elif key_arg == 'cancel_search':
        await state.finish()
        await call.message.edit_text('Выберите руну:', reply_markup=markups.page_mrkups[0])


async def send_rune_day(user_id):
    user_step = await db.get_rune_day_step(user_id)
    day_card_text = texts.days_runes[int(user_step)]
    now_time = datetime.now()
    tomorrow_time = (now_time + timedelta(days=1))
    necessary_time = datetime(year=tomorrow_time.year, month=tomorrow_time.month, day=tomorrow_time.day, hour=0,
                              minute=0, second=0)
    seconds_left = (necessary_time - now_time).total_seconds()
    hours_left = round(seconds_left / 60 // 60)
    minutes_left = round(seconds_left // 60 % 60)
    end_of_text = f"⏳До обновления руны дня осталось: {hours_left} часа {minutes_left} минуты."
    main_text = f'{day_card_text}\n\n{end_of_text}'

    path = Path("data/photos_to_message/day_rune.JPG")
    photo_id = await get_photo_id(path)
    msg = await bot.send_photo(user_id, photo_id)
    await bot.send_message(user_id, main_text, reply_markup=markups.mrkup_for_every_info_btn)
    if isinstance(photo_id, types.InputFile):
        await db.register_photo(path, msg["photo"][0]["file_id"])


@dp.message_handler(lambda message: message.text in markups.titles_all_about_runes_mrkup, state='*')
async def info_menu(message: types.Message, state: FSMContext):
    if message.text == '🧿 Руна дня':
        await send_rune_day(message.from_user.id)
    elif message.text == '🧿 Какие виды рун бывают?':
        path = Path("data/photos_to_message/runes_kinds.JPG")
        photo_id = await get_photo_id(path)
        msg = await message.answer_photo(photo_id, texts.all_about_runes_texts[message.text], reply_markup=markups.mrkup_for_every_info_btn)
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(path, msg["photo"][0]["file_id"])

    elif message.text == '🧿 Что такое руны?':
        path = Path("data/photos_to_message/runes_is_.JPG")
        photo_id = await get_photo_id(path)
        msg = await message.answer_photo(photo_id, texts.all_about_runes_texts[message.text], reply_markup=markups.mrkup_for_every_info_btn)
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(path, msg["photo"][0]["file_id"])
    else:
        await message.answer(texts.all_about_runes_texts[message.text], reply_markup=markups.mrkup_for_every_info_btn)


@dp.message_handler(state=States.search_rune_by_name)
async def search_info_by_name_rune(message: types.Message, state: FSMContext):
    rune_name = "🧿"+message.text.capitalize() if '🧿' not in message.text else message.text.capitalize()
    info_rune = texts.info_about_all_runes.get(rune_name)
    if info_rune is None:
        await message.answer(f'Руна {message.text} не найдена.\nПопробуйте ещё раз', reply_markup=markups.mrkup_to_del)
    else:
        path = info_rune['photo']
        photo_id = await get_photo_id(path)
        msg = await message.answer_photo(photo_id, caption=info_rune['text'], reply_markup=markups.mrkup_to_del)
        if isinstance(photo_id, types.InputFile):
            await db.register_photo(path, msg["photo"][0]["file_id"])


async def sending_message_2_h():
    while True:
        try:
            await asyncio.sleep(12)

            text= f'😊 Я вижу вы отлично поладили с рунами. Приглашаю Вас на полноценный расклад от нашего профессионального рунолога. Она сделает полноценную диагностику и даст рекомендации😎\n\n❗️На сегодня осталось лишь {markdown.hbold("3 бесплатных места")}.\n\nЧтобы получить консультацию или забронировать место просто {markdown.hbold("напишите в л.с")} @RunologyMentor дату рождения.\n\nЖду вас😊'
            photo = await get_photo_id(Path('data/photos_to_message/2h.png'))
            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton("🤩Получить консультацию🤩", url="https://t.me/RunologyMentor"))

            users = await db_sendings.get_users_2h_autosending()
            for user in users:
                try:
                    await bot.send_photo(user, photo=photo, caption=text, parse_mode='html', reply_markup=mrkup)
                    logger.info(f'ID: {user}. Got autosending_2h')
                    await db_sendings.mark_got_2h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            await bot.send_message(1188441997, f'Happened: {ex}')



async def sending_message_24_h():
    while True:
        try:
            await asyncio.sleep(12)

            text = f'❤ Расклад комбинации 🧿 Старшего Футарка {markdown.hbold("по разбору жизненных проблем")} является одной из интересных раскладов для клиентов. Каждый месяц я делаю его {markdown.hbold("бесплатно для 5 счастливчиков")}, которые первыми напишут😉.\n\n❗️Она проводится лишь в определенные лунные сутки. {markdown.hbold("Записать Вас?")}'
            photo = await get_photo_id(Path('data/photos_to_message/24h.png'))

            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton("⚡️Получить расклад бесплатно ⚡️", url="https://t.me/RunologyMentor"))

            users = await db_sendings.get_users_24h_autosending()
            for user in users:
                try:
                    await bot.send_photo(user, photo=photo, caption=text, parse_mode='html', reply_markup=mrkup)
                    logger.info(f'ID: {user}. Got autosending_24h')
                    await db_sendings.mark_got_24h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            await bot.send_message(1188441997, f'Happened: {ex}')


async def sending_message_48_h():
    while True:
        try:
            await asyncio.sleep(12)

            text= f'Каждый месяц есть {markdown.hbold("магические дни")}, когда принятые решения могут кардинально {markdown.hbold("улучшить жизнь.")} На скандинавских рунах можно сделать определенные расклады на конкретную ситуацию или сферу жизни, либо же сразу на все. Но я успею принять в эти волшебные дни лишь 9 человек. {markdown.hbold("Записать Вас?")}\n\nДля составления мне нужны только ваше имя и дата рождения. Жду вас в личных сообщениях @RunologyMentor'
            photo = await get_photo_id(Path('data/photos_to_message/48h.png'))

            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton("⚡️Забронировать бесплатный расклад  ⚡️", url="https://t.me/RunologyMentor"))

            users = await db_sendings.get_users_48h_autosending()
            for user in users:
                try:
                    await bot.send_photo(user, photo=photo, caption=text, parse_mode='html', reply_markup=mrkup)
                    logger.info(f'ID: {user}. Got autosending_text_48h')
                    await db_sendings.mark_got_48h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            await bot.send_message(1188441997, f'Happened: {ex}')


async def sending_message_52_h():
    while True:
        try:
            await asyncio.sleep(12)

            text= f'Сегодня с вами говорят {markdown.hbold("Денежные руны")}. Этот расклад позволит оценить текущее положение дел и заглянуть в будущее, чтобы скорректировать свои действия и получить положительный результат.\n\n{markdown.hbold("Руны могут подсказать:")}\nС какой стороны стоит ожидать опасности для вашего финансового положения.\nПрепятствие, которое вам возможно стоит преодолеть, чтобы обрести деньги, работу и финансовое равновесие в целом.\nПерспективное направление для развития.\nКто может стать надёжным деловым партнёром или каким-то другим способом поможет вам с деньгами.\n\nЧтобы получить такой расклад {markdown.hbold("бесплатно")}, напишите мне в личку @RunologyMentor\nваше имя и дату рождения.'
            photo = await get_photo_id(Path('data/photos_to_message/52h.png'))

            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton("Получить денежный расклад", url="https://t.me/RunologyMentor"))

            users = await db_sendings.get_users_52h_autosending()
            for user in users:
                try:
                    await bot.send_photo(user, photo=photo, caption=text, parse_mode='html', reply_markup=mrkup)
                    logger.info(f'ID: {user}. Got autosending_text_52h')
                    await db_sendings.mark_got_52h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            await bot.send_message(1188441997, f'Happened: {ex}')


async def sending_message_76_h():
    while True:
        try:
            await asyncio.sleep(12)

            text= f'❤️ Наши любовные отношения являются продолжением нас. 😇 Они подсвечивают и отзеркаливают нам: где нам стоит изменить свое состояние, характер или отношение к тем или иным ситуациям. Гармоничные отношения с партнерами являются гарантом {markdown.hbold("внутреннего счастья")} и удачи которую мы привлекаем в других сферах.\nПредлагаю вам {markdown.hbold("любовный расклад")}, который подсветит вам точки роста и способы гармонизации💕 отношений с партнером👩‍❤️‍👨.\n\n🔥 Получить {markdown.hbold("бесплатный расклад на любовь")}💞 можно написав в л.с @RunologyMentor'
            photo = await get_photo_id(Path('data/photos_to_message/76h.png'))

            mrkup = types.InlineKeyboardMarkup()
            mrkup.add(types.InlineKeyboardButton("🥰Расклад на любовь🥰", url="https://t.me/RunologyMentor"))

            users= await db_sendings.get_users_76h_autosending()
            for user in users:
                try:
                    await bot.send_photo(user, photo=photo, caption=text, parse_mode='html', reply_markup=mrkup)
                    logger.info(f'ID: {user}. Got autosending_text_76h')
                    await db_sendings.mark_got_76h_autosending(user)
                    await asyncio.sleep(0.2)
                except (exceptions.BotBlocked, exceptions.UserDeactivated):
                    logger.error(f'ID: {user}. DELETED')
                    await db.delete_user(user)
                except Exception as ex:
                    logger.error(f'got error: {ex}')
        except Exception as ex:
            await bot.send_message(1188441997, f'Happened: {ex}')


async def bf_task(id_: int, sending: SendingData, db_func, skip_if_chat_member: bool = False, only_for_chat_member: bool = False):
    try:

        if skip_if_chat_member or only_for_chat_member:
            chat_member = await bot.get_chat_member(-1002059782974, id_)
            if chat_member.is_chat_member() and skip_if_chat_member:
                return 'skip'
            elif not chat_member.is_chat_member() and only_for_chat_member:
                return 'skip'
            name = chat_member.user.first_name
        else:
            name = None

        if id_ in skip_100_leads:
            return 'skip'

        text = await sending.get_text(bot, id_, name)
        if sending.photo is not None:
            await bot.send_photo(id_, types.InputFile(sending.photo), caption=text, reply_markup=sending.kb,
                                 parse_mode='html', disable_notification=True)
        else:
            await bot.send_message(id_, text=text, reply_markup=sending.kb,
                                   parse_mode='html', disable_web_page_preview=True)
        await db_func(id_)
        sending.count += 1
        logger.success(f'{id_} sending_{sending.uid} text')

    except (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound) as ex:
        logger.error(f'{id_} {ex}')
        logger.exception(f'ID: {id_}. DELETED')
        await db.delete_user(id_)
    except Exception as e:
        logger.error(f'BUG: {e}')
    else:
        return 'success'
    return 'false'


async def sending_newsletter():
    white_day = 24
    print("Начал рассылку")
    while True:
        await asyncio.sleep(2)
        now_time = datetime.now()

        if now_time.day > white_day:
            return

        if now_time.day == white_day and now_time.hour >= 17:
            try:
                tasks = []
                users = [1371617744] + list(await db_sendings.get_users_for_sending_newsletter())
                print(len(users))
                for user in users:
                    logger.info(f"Пытаюсь отправить сообщение рассылки - {user}")
                    try:
                        _s = bf_sending
                        # if _s.count >= 80000:
                        #     break
                        tasks.append(asyncio.create_task(bf_task(user, _s, db_sendings.set_newsletter)))
                        if len(tasks) > 40:
                            print(len(tasks))
                            r = await asyncio.gather(*tasks, return_exceptions=False)
                            await asyncio.wait(tasks)
                            await asyncio.sleep(0.4)
                            logger.success(f"{r.count('success')=}", f"{r.count('false')=}", f"{r.count('skip')=}")
                            tasks.clear()

                    except Exception as ex:
                        logger.error(f'Ошибка в малом блоке sending: {ex}')
                    finally:
                        await asyncio.sleep(0.03)
            except Exception as ex:
                logger.error(f"Ошибка в большом блоке sending - {ex}")
            finally:
                await bot.send_message(1371617744, f"ERROR Рассылка стопнулась.")
                logger.info("Рассылка завершилась")


async def on_startup(_):
    asyncio.create_task(sending_newsletter())
    asyncio.create_task(sending_message_2_h())
    asyncio.create_task(sending_message_24_h())
    asyncio.create_task(sending_message_48_h())
    asyncio.create_task(sending_message_52_h())
    asyncio.create_task(sending_message_76_h())

try:
    a_logger = logging.getLogger('apscheduler.scheduler')
    a_logger.setLevel(logging.DEBUG)
    executor.start_polling(dp, on_startup=on_startup)
finally:
    ...
