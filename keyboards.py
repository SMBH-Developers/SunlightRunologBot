import json
import texts

from aiogram import types
from itertools import islice


class Markups:
    @staticmethod
    def get_titles_from_kb(kb: types.ReplyKeyboardMarkup):
        json_kb = json.loads(kb.as_json())['keyboard']
        titles = []
        for row in json_kb:
            for btn in row:
                titles.append(btn['text'])
        return titles

    @staticmethod
    def chunk(it, size):
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    admin_mrkup = types.InlineKeyboardMarkup()
    admin_mrkup.add(types.InlineKeyboardButton(text='Пользователей всего', callback_data='Admin_Users_Total'))
    admin_mrkup.add(types.InlineKeyboardButton(text='Пользователей за сегодня', callback_data='Admin_Users_For_TODAY'))

    back_admin_mrkup = types.InlineKeyboardMarkup()
    back_admin_mrkup.add(types.InlineKeyboardButton(text='⬅️ В меню админа', callback_data='Admin_BACK'))
    # *********************************************************************************
    mrkup_to_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mrkup_to_start.add(types.KeyboardButton(text='⚡️ Расклад⚡️'))
    titles_mrkup_to_start = get_titles_from_kb(mrkup_to_start)
    # *********************************************************************************
    combinations_mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    combinations_mrkup.add(types.KeyboardButton('Комбинация №1'), types.KeyboardButton('Комбинация №2'))
    combinations_mrkup.add(types.KeyboardButton('Комбинация №3'), types.KeyboardButton('Комбинация №4'))
    titles_of_combination_mrkup = get_titles_from_kb(combinations_mrkup)
    # *********************************************************************************
    menu_mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu_mrkup.add(types.KeyboardButton('🧿Все о рунах'))
    menu_mrkup.add(types.KeyboardButton('ℹ️Расшифровка всех рун'),
                   types.KeyboardButton('📚Обучение руническому раскладу'))
    menu_mrkup.add(types.KeyboardButton('🤩Получить бесплатный расклад🤩'))
    titles_of_menu_mrkup = get_titles_from_kb(menu_mrkup)
    # *********************************************************************************
    mrkup_to_del = types.InlineKeyboardMarkup()
    mrkup_to_del.add(types.InlineKeyboardButton('🗑 Удалить сообщение', callback_data='DELETE'))
    # *********************************************************************************
    values_of_all_info_runes = chunk(list(texts.info_about_all_runes.keys()), 6)
    page_mrkups = []
    for index_page_mrkup, page_mrkup in enumerate(values_of_all_info_runes):
        count = 6 * index_page_mrkup
        main_mrkup = types.InlineKeyboardMarkup()
        main_mrkup.add(
            types.InlineKeyboardButton('🔎Поиск руны по названию', callback_data='info_runes?search_by_name=none'))
        for couple_btns in chunk(page_mrkup, 2):
            btns = []
            text_btn_1, text_btn_2 = couple_btns
            assert type(text_btn_1) is str and type(text_btn_2) is str
            btns.append(types.InlineKeyboardButton(text=text_btn_1, callback_data=f'info_runes?choose_rune={count}'))
            count += 1
            btns.append(types.InlineKeyboardButton(text=text_btn_2, callback_data=f'info_runes?choose_rune={count}'))
            count += 1
            main_mrkup.add(*btns)
        down_btns = []
        if index_page_mrkup != 0:
            down_btns.append(
                types.InlineKeyboardButton('Назад', callback_data=f'info_runes?next_page={index_page_mrkup - 1}'))
        if index_page_mrkup != 3:
            down_btns.append(
                types.InlineKeyboardButton('Далее', callback_data=f'info_runes?next_page={index_page_mrkup + 1}'))
        main_mrkup.add(*down_btns)
        page_mrkups.append(main_mrkup)
    cancel_searching_rune_by_name = types.InlineKeyboardMarkup()
    cancel_searching_rune_by_name.add(
        types.InlineKeyboardButton(text='⛔️ Отмена ввода', callback_data='info_runes?cancel_search=none'))
    # Меню: Всё о рунах
    all_about_runes_mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    all_about_runes_mrkup.add(types.KeyboardButton('🧿 Для чего нужны руны?'), types.KeyboardButton('🧿 Что такое руны?'))
    all_about_runes_mrkup.add(types.KeyboardButton('🧿 Руна дня'), types.KeyboardButton('🧿 Можно ли гадать на рунах?'))
    all_about_runes_mrkup.add(types.KeyboardButton('🧿 Какие виды рун бывают?'),
                              types.KeyboardButton('🧿 Какая руна символизирует здоровье?'))
    all_about_runes_mrkup.add(types.KeyboardButton('🧿 Что можно увидеть на рунах?'),
                              types.KeyboardButton('🧿 Какая разница между рунами и Таро?'))
    all_about_runes_mrkup.add(types.KeyboardButton('🧿 Что означает пустая руна в раскладе?'))
    all_about_runes_mrkup.add(types.KeyboardButton('👈Обратно'))
    titles_all_about_runes_mrkup = get_titles_from_kb(all_about_runes_mrkup)
    # *********************************************************************************
    mrkup_for_every_info_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mrkup_for_every_info_btn.add(types.KeyboardButton('👈Назад'))
    # *********************************************************************************
    back_to_main_menu_mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_to_main_menu_mrkup.add(types.KeyboardButton('👈Обратно'))
    # *********************************************************************************
    to_our_autoanswer_mrkup = types.InlineKeyboardMarkup()
    to_our_autoanswer_mrkup.add(
        types.InlineKeyboardButton(text='🔮Получить рунический расклад', url="https://t.me/RunologyMentor"))
    # *********************************************************************************
    study_rune_mrkup_on_page_1 = types.InlineKeyboardMarkup()
    study_rune_mrkup_on_page_1.add(types.InlineKeyboardButton('Далее ➡️', callback_data='rune_study_to_page_2'))
    # *********************************************************************************
    study_rune_mrkup_on_page_2 = types.InlineKeyboardMarkup()
    study_rune_mrkup_on_page_2.add(types.InlineKeyboardButton('🗃️Варианты расклада', callback_data='studies_options'))
    # *********************************************************************************
    options_studies_rune_mrkup = types.InlineKeyboardMarkup()
    options_studies_rune_mrkup.add(types.InlineKeyboardButton('Случайная руна', callback_data='check_study?index=0'))
    options_studies_rune_mrkup.add(types.InlineKeyboardButton('Метод трёх Норн', callback_data='check_study?index=1'))
    options_studies_rune_mrkup.add(
        types.InlineKeyboardButton('Четырёхрунный расклад', callback_data='check_study?index=2'))
    options_studies_rune_mrkup.add(
        types.InlineKeyboardButton('Расклад в пять рун', callback_data='check_study?index=3'))
    options_studies_rune_mrkup.add(types.InlineKeyboardButton('Расклад «Крест»', callback_data='check_study?index=4'))
    options_studies_rune_mrkup.add(
        types.InlineKeyboardButton('Шестирунный расклад', callback_data='check_study?index=5'))
    options_studies_rune_mrkup.add(
        types.InlineKeyboardButton('Расклад в семь рун', callback_data='check_study?index=6'))
    # *********************************************************************************
    mrkup_under_every_study_rune = types.InlineKeyboardMarkup()
    mrkup_under_every_study_rune.add(types.InlineKeyboardButton('⬅️Назад', callback_data='studies_options'))
    # *********************************************************************************
