import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QMainWindow, QFormLayout, QDialog, QDesktopWidget, QDateTimeEdit
import pymysql
from datetime import datetime
from database import Query

class CreatePollWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Create Poll')
        self.layout = QFormLayout()

        self.start_date_input = QDateTimeEdit(self)
        self.end_date_input = QDateTimeEdit(self)
        self.question_input = QLineEdit(self)

        self.layout.addRow('Start Date:', self.start_date_input)
        self.layout.addRow('End Date:', self.end_date_input)
        self.layout.addRow('Question:', self.question_input)

        self.create_poll_button = QPushButton('Create Poll', self)
        self.create_poll_button.clicked.connect(self.create_poll)
        self.layout.addWidget(self.create_poll_button)

        self.setLayout(self.layout)

    def create_poll(self):
            start_date = self.start_date_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
            end_date = self.end_date_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
            question = self.question_input.text()

            if start_date and end_date and question:
                try:
                    with self.parent.connection.cursor() as cursor:
                        # Get current date and time
                        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        # Insert poll into database
                        poll_insert_query = "INSERT INTO POLL (START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE) VALUES (%s, %s, %s, 0, 0, %s)"
                        cursor.execute(poll_insert_query, (current_datetime, current_datetime, question, current_datetime))

                        # Get the poll_id of the inserted poll
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        poll_id = cursor.fetchone()['LAST_INSERT_ID()']

                        # Insert items into ITEM table
                        item_insert_query = "INSERT INTO ITEM (POLL_ID, ITEM_TEXT, VOTE_COUNT) VALUES (%s, %s, 0)"
                        items = ['Item 1', 'Item 2', 'Item 3']  # You can customize the list of items
                        item_data = [(poll_id, item) for item in items]
                        cursor.executemany(item_insert_query, item_data)

                        # Commit the transaction
                        self.parent.connection.commit()
                        print(f"Poll created with question: '{question}' and items: {items}")

                        # Close the window after creating the poll
                        self.close()
                except pymysql.MySQLError as e:
                    print(f"Database error: {e}")
            else:
                print("Please enter start date, end date, and question.")

class ViewPollsWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('View Polls')
        self.layout = QVBoxLayout()

        try:
            with self.parent.connection.cursor() as cursor:
                # Retrieve all polls from the POLL table
                poll_query = "SELECT * FROM POLL"
                cursor.execute(poll_query)
                polls = cursor.fetchall()

                for poll in polls:
                    poll_id = poll['POLL_ID']
                    question = poll['QUESTION']

                    poll_button = QPushButton(question, self)
                    poll_button.clicked.connect(lambda _, pid=poll_id: self.show_vote_items(pid))
                    self.layout.addWidget(poll_button)

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

        self.setLayout(self.layout)

    def show_vote_items(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                # Retrieve items for the selected poll
                item_query = "SELECT * FROM ITEM WHERE POLL_ID = %s"
                cursor.execute(item_query, (poll_id,))
                items = cursor.fetchall()

                # Display the items in a new window
                vote_item_window = VoteItemWindow(self.parent, items, poll_id)
                vote_item_window.exec_()
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

class VotePollWindow(QDialog):
    def __init__(self, parent, items, poll_id):
        super().__init__()
        self.parent = parent
        self.items = items
        self.poll_id = poll_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Vote Poll')
        self.layout = QVBoxLayout()

        for item in self.items:
            item_id = item['ITEM_ID']
            item_text = item['ITEM_TEXT']
            vote_count = item['VOTE_COUNT']

            item_button = QPushButton(f"Item ID: {item_id}, Item Text: {item_text}, Vote Count: {vote_count}", self)
            item_button.clicked.connect(lambda _, iid=item_id: self.vote_for_item(iid))
            self.layout.addWidget(item_button)

        self.setLayout(self.layout)

    def vote_for_item(self, item_id):
        try:
            with self.parent.connection.cursor() as cursor:
                # Update vote count for the specified item
                update_vote_query = "UPDATE ITEM SET VOTE_COUNT = VOTE_COUNT + 1 WHERE ITEM_ID = %s"
                cursor.execute(update_vote_query, (item_id,))

                # Update total vote count for the poll
                update_poll_total_query = "UPDATE POLL SET POLLTOTAL = POLLTOTAL + 1 WHERE POLL_ID = %s"
                cursor.execute(update_poll_total_query, (self.poll_id,))

                # Commit the transaction
                self.parent.connection.commit()
                print(f"Vote recorded for Item ID: {item_id}")

                # Refresh the items in the current window
                self.refresh_items()

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

    def refresh_items(self):
        # Close the current window and reopen it with updated data
        self.close()
        view_poll_window = VotePollWindow(self.parent, self.items, self.poll_id)
        view_poll_window.exec_()
        

class VoteItemWindow(QDialog):
    def __init__(self, parent, items, poll_id):
        super().__init__()
        self.parent = parent
        self.items = items
        self.poll_id = poll_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Vote for Item')
        self.layout = QVBoxLayout()

        for item in self.items:
            item_id = item['ITEM_ID']
            item_text = item['ITEM_TEXT']
            vote_count = item['VOTE_COUNT']

            item_label = QLabel(f"Item ID: {item_id}, Item Text: {item_text}, Vote Count: {vote_count}")
            self.layout.addWidget(item_label)

        self.item_id_input = QLineEdit(self)
        self.layout.addWidget(self.item_id_input)

        self.vote_button = QPushButton('Vote', self)
        self.vote_button.clicked.connect(self.vote_for_item)
        self.layout.addWidget(self.vote_button)

        self.setLayout(self.layout)

    def vote_for_item(self):
        item_id = self.item_id_input.text()

        if item_id:
            try:
                with self.parent.connection.cursor() as cursor:
                    # Update vote count for the specified item
                    update_vote_query = "UPDATE ITEM SET VOTE_COUNT = VOTE_COUNT + 1 WHERE ITEM_ID = %s"
                    cursor.execute(update_vote_query, (item_id,))

                    # Update total vote count for the poll
                    update_poll_total_query = "UPDATE POLL SET POLLTOTAL = POLLTOTAL + 1 WHERE POLL_ID = %s"
                    cursor.execute(update_poll_total_query, (self.poll_id,))

                    # Commit the transaction
                    self.parent.connection.commit()
                    print(f"Vote recorded for Item ID: {item_id}")

                    # Close the window after voting
                    self.close()

            except pymysql.MySQLError as e:
                print(f"Database error: {e}")

        else:
            print("Please enter Item ID.")


class LoginScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Login')
        self.layout = QVBoxLayout()

        self.login_label = QLabel('Login:')
        self.login_text = QLineEdit(self)
        self.login_password = QLineEdit(self)
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.parent.login)
        self.layout.addWidget(self.login_label)
        self.layout.addWidget(self.login_text)
        self.layout.addWidget(self.login_password)
        self.layout.addWidget(self.login_button)

        self.login_result_label = QLabel(self)
        self.layout.addWidget(self.login_result_label)

        self.setLayout(self.layout)

    def show_login_result(self, success):
        if success:
            self.login_result_label.setText("Login successful")
        else:
            self.login_result_label.setText("Login failed")
            
class VotePollWindow(QDialog):
    def __init__(self, parent, polls):
        super().__init__()
        self.parent = parent
        self.polls = polls
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Vote Poll')
        self.layout = QVBoxLayout()

        for poll in self.polls:
            try:
                question = poll['QUESTION']
            except KeyError:
                question = "Question not available"

            poll_button = QPushButton(question, self)
            poll_button.clicked.connect(lambda _, pid=poll['POLL_ID']: self.show_vote_items(pid))
            self.layout.addWidget(poll_button)

        self.setLayout(self.layout)

    def show_vote_items(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                # Retrieve items for the selected poll
                item_query = "SELECT * FROM ITEM WHERE POLL_ID = %s"
                cursor.execute(item_query, (poll_id,))
                items = cursor.fetchall()

                # Display the items in a new window
                vote_item_window = VoteItemWindow(self.parent, items, poll_id)
                vote_item_window.exec_()
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")


class MainMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Main Menu')
        self.layout = QVBoxLayout()

        self.create_poll_button = QPushButton('Create Poll', self)
        self.create_poll_button.clicked.connect(self.show_create_poll)
        self.layout.addWidget(self.create_poll_button)

        self.view_polls_button = QPushButton('View Polls', self)
        self.view_polls_button.clicked.connect(self.show_view_polls)
        self.layout.addWidget(self.view_polls_button)

        # 변경: Vote 버튼을 Quit 버튼으로 변경하고, 클릭 시 프로그램 종료
        self.quit_button = QPushButton('Quit', self)
        self.quit_button.clicked.connect(self.quit_program)
        self.layout.addWidget(self.quit_button)

        self.setLayout(self.layout)

    def show_create_poll(self):
        create_poll_window = CreatePollWindow(self.parent)
        create_poll_window.exec_()

    def show_view_polls(self):
        view_polls_window = ViewPollsWindow(self.parent)
        view_polls_window.exec_()

    # 변경: Vote 버튼 클릭 시 프로그램 종료
    def quit_program(self):
        self.parent.close()

class AdditionalFields(QWidget):
    def __init__(self, parent, functionality):
        super().__init__()
        self.parent = parent
        self.functionality = functionality
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Additional Fields')
        self.layout = QVBoxLayout()

        self.additional_label = QLabel('Additional Fields:')
        self.additional_text = QTextEdit(self)
        self.layout.addWidget(self.additional_label)
        self.layout.addWidget(self.additional_text)

        self.execute_button = QPushButton('Execute', self)
        self.execute_button.clicked.connect(self.execute_functionality)
        self.layout.addWidget(self.execute_button)

        self.setLayout(self.layout)

    def execute_functionality(self):
        if self.functionality == 'Create Poll':
            self.parent.create_poll(self.additional_text.toPlainText())
        elif self.functionality == 'Vote':
            self.parent.vote(self.additional_text.toPlainText())
        else:
            print("Invalid functionality selected.")

        self.close()

class VotingSystem(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize database connection
        self.connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='qwer1234',
            db='voting',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        # Create tables if they don't exist
        self.create_tables()

        # Current user ID (logged in user)
        self.user_id = None

        # Create UI
        self.init_ui()
        
    def create_tables(self):
        try:
            with self.connection.cursor() as cursor:
                # Check if ACCOUNT table exists
                cursor.execute("SHOW TABLES LIKE 'ACCOUNT'")
                if not cursor.fetchone():
                    # ACCOUNT table does not exist, create it
                    self.create_account_table(cursor)

                # Check if POLL table exists
                cursor.execute("SHOW TABLES LIKE 'POLL'")
                if not cursor.fetchone():
                    # POLL table does not exist, create it
                    self.create_poll_table(cursor)

                # Check if ITEM table exists
                cursor.execute("SHOW TABLES LIKE 'ITEM'")
                if not cursor.fetchone():
                    # ITEM table does not exist, create it
                    self.create_item_table(cursor)

                # Commit the transaction
                self.connection.commit()

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
        
    def create_item_table(self, cursor):
        query = '''
        CREATE TABLE ITEM (
            ITEM_ID int(11) NOT NULL AUTO_INCREMENT,
            POLL_ID int(11) NOT NULL,
            ITEM_TEXT varchar(255) NOT NULL,
            VOTE_COUNT int(11) NOT NULL DEFAULT 0,
            PRIMARY KEY (ITEM_ID, POLL_ID),
            FOREIGN KEY (POLL_ID) REFERENCES POLL(POLL_ID)
        ) AUTO_INCREMENT=1
        '''
        cursor.execute(query)

    def create_poll_table(self, cursor):
        query = '''
        CREATE TABLE POLL (
            POLL_ID int(11) NOT NULL AUTO_INCREMENT,
            START_DATE varchar(50) NOT NULL,
            END_DATE varchar(50),
            ITEMCOUNT int(11) NOT NULL DEFAULT 0,
            QUESTION varchar(30),
            POLLTOTAL int(11) NOT NULL DEFAULT 0,
            REGDATE varchar(50),
            PRIMARY KEY(POLL_ID)
        ) AUTO_INCREMENT=1
        '''
        cursor.execute(query)

    def create_account_table(self, cursor):
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


    def init_ui(self):
        self.setWindowTitle('Voting System')

        # Create instances of different screens
        self.login_screen = LoginScreen(self)
        self.main_menu = MainMenu(self)

        # Set the main layout
        self.layout = QVBoxLayout()

        # Add the login screen initially
        self.layout.addWidget(self.login_screen)

        # Create a central widget to hold the layout
        central_widget = QWidget(self)
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Center the window on the screen
        self.center_on_screen()

    def center_on_screen(self):
        # Calculate the center position of the screen
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def login(self):
        username = self.login_screen.login_text.text()
        password = self.login_screen.login_password.text()

        if username and password:
            try:
                with self.connection.cursor() as cursor:
                    # Check if the user exists
                    user_query = "SELECT * FROM ACCOUNT WHERE USERNAME = %s"
                    cursor.execute(user_query, (username,))
                    existing_user = cursor.fetchone()

                    if existing_user:
                        # User exists, check the password
                        if existing_user['PASSWORD'] == password:
                            self.user_id = existing_user['ACCOUNT_ID']
                            print(f"Login successful for user '{username}'")

                            # Remove the login screen and show the main menu
                            self.layout.removeWidget(self.login_screen)
                            self.layout.addWidget(self.main_menu)
                            self.login_screen.deleteLater()

                            # Show login result on the login screen
                            self.login_screen.show_login_result(True)
                        else:
                            print(f"Login failed for user '{username}': Incorrect password")
                            # Show login result on the login screen
                            self.login_screen.show_login_result(False)
                    else:
                        # User does not exist, create a new account
                        create_account_query = "INSERT INTO ACCOUNT (USERNAME, PASSWORD) VALUES (%s, %s)"
                        cursor.execute(create_account_query, (username, password))
                        self.connection.commit()

                        # Retrieve the newly created user
                        cursor.execute(user_query, (username,))
                        new_user = cursor.fetchone()

                        self.user_id = new_user['ACCOUNT_ID']
                        print(f"New account created and logged in for user '{username}'")

                        # Remove the login screen and show the main menu
                        self.layout.removeWidget(self.login_screen)
                        self.layout.addWidget(self.main_menu)
                        self.login_screen.deleteLater()

                        # Show login result on the login screen
                        self.login_screen.show_login_result(True)

            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("Please enter both username and password.")

    def create_poll(self, question):
        if question and self.user_id:
            try:
                with self.connection.cursor() as cursor:
                    # Get current date and time
                    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Insert poll into database
                    poll_insert_query = "INSERT INTO POLL (START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE) VALUES (%s, %s, %s, 0, 0, %s)"
                    cursor.execute(poll_insert_query, (current_datetime, current_datetime, question, current_datetime))

                    # Commit the transaction
                    self.connection.commit()
                    print(f"Poll created with question: '{question}'")
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("Please enter a poll question and make sure you are logged in.")

    def vote(self, item_text):
        if item_text and self.user_id:
            try:
                with self.connection.cursor() as cursor:
                    # Check if the poll exists
                    poll_query = "SELECT * FROM POLL WHERE QUESTION = %s"
                    cursor.execute(poll_query, (item_text,))
                    poll = cursor.fetchone()

                    if poll:
                        poll_id = poll['POLL_ID']

                        # Insert the vote
                        item_insert_query = "INSERT INTO ITEM (POLL_ID, ITEM_TEXT, VOTE_COUNT) VALUES (%s, %s, 1)"
                        cursor.execute(item_insert_query, (poll_id, item_text))

                        # Update the item count
                        item_count_query = "UPDATE POLL SET ITEMCOUNT = (SELECT COUNT(*) FROM ITEM WHERE POLL_ID = %s) WHERE POLL_ID = %s"
                        cursor.execute(item_count_query, (poll_id, poll_id))

                        # Commit the transaction
                        self.connection.commit()
                        print(f"Vote recorded for '{item_text}' in poll '{item_text}'")
                    else:
                        print(f"Poll '{item_text}' not found.")
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("Please enter both the poll question and your username.")

    def closeEvent(self, event):
        # Close the database connection when the application is closed
        if self.connection:
            self.connection.close()

def main():
    app = QApplication(sys.argv)
    window = VotingSystem()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
