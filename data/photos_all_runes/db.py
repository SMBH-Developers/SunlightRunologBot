import pymysql
import random

from typing import Union
from pymysql.connections import Connection


class Database:

    @staticmethod
    def connect():
        """

        :return: Connection
        """

        connection: Connection = pymysql.connect(
            user="root", passwd="root", host="localhost", database='TIZIO_RUNES_BOT_1',  # TODO: Database
            port=3306, autocommit=True)
        return connection

    def register_user(self, user_id):
        random_value = random.choice(list(range(0, 7)))
        query_to_reg_user = f"INSERT INTO Users (User_ID, Rune_Day_Step) VALUES ({user_id}, {random_value});"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query_to_reg_user)

    def check_if_user_exists(self, user_id: Union[int, str]) -> bool:
        query_to_get_user = f"SELECT User_ID FROM Users WHERE User_ID={user_id} LIMIT 1;"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query_to_get_user)
                user = cursor.fetchone()
                # None, (id,)
        if not user:
            return False
        else:
            return True

    def check_if_user_chose_combination(self, user_id) -> bool:
        query = f"SELECT Chose_Combination FROM Users WHERE User_ID={user_id} LIMIT 1;"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                did_choose_combination = cursor.fetchone()[0]
        return did_choose_combination

    def set_user_chose_combination(self, user_id, num):
        if num is not None:
            num = int(num)
        query = f"UPDATE Users SET Chose_Combination=%s WHERE User_ID={user_id};"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (num, ))

    def get_rune_day_step(self, user_id):
        query = f"SELECT Rune_Day_Step from Users where User_ID={user_id} LIMIT 1;"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rune_step = cursor.fetchone()[0]
        return rune_step

    def update_card_day_step(self):
        query_1 = "UPDATE Users SET Rune_Day_Step=IF(Rune_Day_Step=6, 0, Rune_Day_Step+1);"
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query_1)
