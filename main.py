import pymysql
import numpy as np
import PyQt5
from database import Query

db = pymysql.connect(host='127.0.0.1', port=3306, user="root", password='qwer1234', db='voting', charset='utf8')

cursor = db.cursor()

Query.ACCOUNT_CREATE(cursor)
Query.ACCOUNT_INSERT(cursor, "admin", "admin", 0, "127.0.0.1")


Query.POLL_CREATE(cursor)

Query.POLL_INSERT(cursor, "2023-12-08", "2023-12-12", "동아리 종강총회", 0, 0, "2023-12-08")
Query.POLL_INSERT(cursor, "2023-12-09", "2023-12-11", "동아리 종강회식", 0, 0, "2023-12-08")

Query.ITEM_CREATE(cursor)

Query.ITEM_INSERT(cursor, 1, "12/15", 0)
Query.ITEM_INSERT(cursor, 1, "12/16", 0)
Query.ITEM_INSERT(cursor, 1, "12/17", 0)
Query.ITEM_INSERT(cursor, 2, "12/15", 0)
Query.ITEM_INSERT(cursor, 2, "12/16", 0)
Query.ITEM_INSERT(cursor, 2, "12/17", 0)
Query.ITEM_INSERT(cursor, 2, "12/18", 0)

db.commit()

db.close()

