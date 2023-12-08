import pymysql

def POLL_CREATE(cursor):
    query1 = "DROP TABLE IF EXISTS ITEM;"
    cursor.execute(query1)
    query2 = "DROP TABLE IF EXISTS POLL;"
    cursor.execute(query2)
    query = '''
    CREATE TABLE POLL (
        POLL_ID int(11) NOT NULL AUTO_INCREMENT,
        START_DATE varchar(50) NOT NULL,
        END_DATE varchar(50),
        ITEMCOUNT int(11),
        QUESTION varchar(30),
        POLLTOTAL int(11),
        REGDATE varchar(50),
        PRIMARY KEY(POLL_ID)
    ) AUTO_INCREMENT=1
    '''
    cursor.execute(query)

def POLL_INSERT(cursor, START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE):
    query = "INSERT INTO POLL (START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE))

def ACCOUNT_CREATE(cursor):
    query1 = "DROP TABLE IF EXISTS ACCOUNT;"
    cursor.execute(query1)
    query = '''
    CREATE TABLE ACCOUNT (
        ACCOUNT_ID int(11) NOT NULL AUTO_INCREMENT,
        USERNAME varchar(20) NOT NULL,
        PASSWORD varchar(20) NOT NULL,
        IS_BANNED tinyint(1) NOT NULL DEFAULT '0',
        SESSION_IP varchar(20),
        PRIMARY KEY(ACCOUNT_ID)
    ) AUTO_INCREMENT=1
    '''
    cursor.execute(query)

def ACCOUNT_INSERT(cursor, USERNAME, PASSWORD, IS_BANNED, SESSION_IP):
    query = "INSERT INTO ACCOUNT (USERNAME, PASSWORD, IS_BANNED, SESSION_IP) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (USERNAME, PASSWORD, IS_BANNED, SESSION_IP))
    

def ITEM_CREATE(cursor):
    query1 = "DROP TABLE IF EXISTS ITEM;"
    cursor.execute(query1)
    query = '''
    CREATE TABLE ITEM (
        ITEM_ID int(11) NOT NULL AUTO_INCREMENT,
        POLL_ID int(11) NOT NULL,
        ITEM_TEXT varchar(255) NOT NULL,
        VOTE_COUNT int(11),
        PRIMARY KEY (ITEM_ID, POLL_ID),
        FOREIGN KEY (POLL_ID) REFERENCES POLL(POLL_ID)
    ) AUTO_INCREMENT=1
    '''
    cursor.execute(query)

def ITEM_INSERT(cursor, POLL_ID, ITEM_TEXT, VOTE_COUNT):
    # 아이템을 추가
    query_insert_item = "INSERT INTO ITEM (POLL_ID, ITEM_TEXT, VOTE_COUNT) VALUES (%s, %s, %s)"
    cursor.execute(query_insert_item, (POLL_ID, ITEM_TEXT, VOTE_COUNT))

    # POLL_ID에 해당하는 ITEMCOUNT 업데이트
    query_update_item_count = "UPDATE POLL SET ITEMCOUNT = (SELECT COUNT(*) FROM ITEM WHERE POLL_ID = %s) WHERE POLL_ID = %s"
    cursor.execute(query_update_item_count, (POLL_ID, POLL_ID))
    
def POLL_DELETE_BY_ID(cursor, poll_id):
    query_delete_item = "DELETE FROM ITEM WHERE POLL_ID = %s"
    cursor.execute(query_delete_item, (poll_id,))

    query_delete_poll = "DELETE FROM POLL WHERE POLL_ID = %s"
    cursor.execute(query_delete_poll, (poll_id,))

def ACCOUNT_DELETE_BY_ID(cursor, account_id):
    query_delete_account = "DELETE FROM ACCOUNT WHERE ACCOUNT_ID = %s"
    cursor.execute(query_delete_account, (account_id,))

def ITEM_DELETE_BY_ID(cursor, item_id, poll_id):
    query_delete_item = "DELETE FROM ITEM WHERE ITEM_ID = %s AND POLL_ID = %s"
    cursor.execute(query_delete_item, (item_id, poll_id))

    query_update_item_count = "UPDATE POLL SET ITEMCOUNT = (SELECT COUNT(*) FROM ITEM WHERE POLL_ID = %s) WHERE POLL_ID = %s"
    cursor.execute(query_update_item_count, (poll_id, poll_id))
