import pymysql
import asyncio
import asyncssh
import aiomysql
import json

from sqlalchemy.sql.expression import update

from src.models import User, async_session

# *mdb - mariadb


async def get_users_from_mdb():
    async with asyncssh.connect(host='45.132.106.153', port=22, username='root', password='M0lcnzaj1jdb', known_hosts=None) as conn:
        async with conn.forward_local_port('127.0.0.1', 0, '127.0.0.1', 3306) as tunnel:
            local_bind_port = tunnel.get_port()
            print('used query')
            query = "SELECT User_ID, Registration_Date, Chose_Combination, Rune_Day_Step, Got_24h_autosending, Got_48h_autosending FROM Users ;"
            connection = await aiomysql.connect(host='localhost',  user='root', password='root', db='TIZIO_RUNES_BOT_1', port=local_bind_port)
            cur = await connection.cursor()
            await cur.execute(query)
            data = await cur.fetchall()
            await cur.close()
            connection.close()
    return data


async def fill_psql_from_mdb_data(data):
    users = [User(id=int(user[0]), registration_date=user[1],
                  chosen_combination=user[2], rune_day_step=user[3],
                  got_24h_autosending=user[4], got_48h_autosending=user[5]
                  ) for user in data]
    async with async_session() as session:
        session.add_all(users)
        await session.commit()


async def main():
    # await update_stages_via_ignore_list()
    data = await get_users_from_mdb()
    await fill_psql_from_mdb_data(data)


if __name__ == '__main__':
    asyncio.run(main())

