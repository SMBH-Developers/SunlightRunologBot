from ._engine import async_session
from ._models import User, File

from datetime import date
from pathlib import Path

from sqlalchemy.sql.expression import select, update, delete, func


async def registrate_if_not_exists(id_: int):
    async with async_session() as session:
        exists = (await session.execute(select(User.id).where(User.id == id_).limit(1))).one_or_none()
        if exists is None:
            user = User(id=id_)
            session.add(user)
            await session.commit()


async def delete_user(id_: int):
    query = delete(User).where(User.id == id_)

    async with async_session() as session:
        await session.execute(query)
        await session.commit()


def check_if_user_chose_combination(self, user_id) -> bool:
    query = f"SELECT Chose_Combination FROM Users WHERE User_ID={user_id} LIMIT 1;"
    with self.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            did_choose_combination = cursor.fetchone()[0]
    return did_choose_combination


async def set_user_chose_combination(id_: int, num: int):
    query = update(User).where(User.id == id_).values(chosen_combination=num)

    async with async_session() as session:
        await session.execute(query)
        await session.commit()


async def get_rune_day_step(id_: int) -> int:
    query = select(User.rune_day_step).where(User.id == id_).limit(1)
    async with async_session() as session:
        rune_day_step = (await session.execute(query)).scalar_one_or_none()
    return rune_day_step


async def get_photo_id(path: Path | str):
    if isinstance(path, Path):
        path = str(path)

    query = select(File.telegram_id).where(File.path == path).limit(1)
    async with async_session() as session:
        photo_id = (await session.execute(query)).scalar_one_or_none()
    return photo_id


async def register_photo(path: Path | str, telegram_id: str):
    if isinstance(path, Path):
        path = str(path)

    async with async_session() as session:
        file = File(path=path, telegram_id=telegram_id)
        session.add(file)
        await session.commit()


async def get_count_all_users() -> int:
    query = select(func.count('*')).select_from(User)
    async with async_session() as session:
        count = (await session.execute(query)).scalar_one()
    return count


async def users_for_today() -> int:
    query = select(func.count('*')).select_from(User).where(func.DATE(User.registration_date) == date.today())
    async with async_session() as session:
        count = (await session.execute(query)).scalar_one()
    return count
