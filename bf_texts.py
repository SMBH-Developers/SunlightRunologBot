from dataclasses import dataclass, field
from string import Template

from aiogram import types, Bot
from aiogram.utils import markdown as m


@dataclass
class SendingData:
    uid: str
    text: str | Template
    url: str
    btn_title: str
    photo: str | None = None

    kb: types.InlineKeyboardMarkup = field(init=False)
    count: int = field(init=False)

    async def get_text(self, bot: Bot, user_id: int, name: str = None):
        if isinstance(self.text, str):
            return self.text
        else:
            if name is None:
                chat_member = await bot.get_chat_member(user_id, user_id)
                name = chat_member.user.first_name
            name = m.quote_html(name)
            return self.text.substitute(name=name)

    def __post_init__(self):
        self.kb = types.InlineKeyboardMarkup()
        self.kb.add(types.InlineKeyboardButton(self.btn_title, url=self.url))
        self.count = 0


bf_sending = SendingData("sending_24_april",
                         Template(f'ВОЛШЕБНАЯ ДЕНЕЖНАЯ 💸 ТАБЛЕТКА НАЙДЕНА\n\n💎24.04.2024💎\nЕсли Вы давно ищите лекарство или волшебную таблетку, сегодня у Вас есть такой шанс, сегодня ЗЕРКАЛЬНАЯ ДАТА. самый мощный энергетический день и он поможет Вам проблему с деньгами раз и на всегда\n\nПишите мне в личные сообщение слово " ЗЕРКАЛО "\n➡️  @your_gurusoul\nРешение которое Вы всю жизнь искали ждет Вас 🙌🏻'),
                         url="https://t.me/your_gurusoul",
                         btn_title="НАПИСАТЬ"
                         )

