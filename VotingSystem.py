import sys
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QMessageBox, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QMainWindow, QFormLayout, QDialog, QDesktopWidget, QDateTimeEdit
from PyQt5.QtCore import Qt
import pymysql
from datetime import datetime
from database import Query
import logging

class ManagePollItemsWindow(QDialog):
    def __init__(self, parent, poll_id):
        super().__init__()
        self.parent = parent
        self.poll_id = poll_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Manage Poll Items')
        self.layout = QVBoxLayout()
        
        # List of poll items
        self.items_list = QListWidget(self)
        self.load_items()
        self.layout.addWidget(self.items_list)

        # Input for adding or editing items
        self.item_input = QLineEdit(self)
        self.layout.addWidget(self.item_input)

        # Buttons for adding, editing, and deleting items
        self.add_item_button = QPushButton('Add Item', self)
        self.add_item_button.clicked.connect(self.add_item)
        self.edit_item_button = QPushButton('Edit Selected Item', self)
        self.edit_item_button.clicked.connect(self.edit_item)
        self.delete_item_button = QPushButton('Delete Selected Item', self)
        self.delete_item_button.clicked.connect(self.delete_item)
        self.layout.addWidget(self.add_item_button)
        self.layout.addWidget(self.edit_item_button)
        self.layout.addWidget(self.delete_item_button)

        self.setLayout(self.layout)

    def load_items(self):
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT ITEM_ID, ITEM_TEXT FROM ITEM WHERE POLL_ID = %s", (self.poll_id,))
                for item in cursor.fetchall():
                    self.items_list.addItem(f"{item['ITEM_TEXT']}")
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
    
    def add_item(self):
        item_text = self.item_input.text()
        if item_text:
            try:
                with self.parent.connection.cursor() as cursor:
                    # Insert new item into the ITEM table
                    insert_query = "INSERT INTO ITEM (POLL_ID, ITEM_TEXT, VOTE_COUNT) VALUES (%s, %s, 0)"
                    cursor.execute(insert_query, (self.poll_id, item_text))
                    self.parent.connection.commit()
                    print(f"Item '{item_text}' added to poll ID {self.poll_id}")

                    # Update UI
                    self.items_list.addItem(item_text)
                    self.item_input.clear()
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")

    def edit_item(self):
        selected_item = self.items_list.currentItem()
        if selected_item:
            new_text = self.item_input.text()
            if new_text:
                try:
                    with self.parent.connection.cursor() as cursor:
                        # Update the selected item
                        update_query = "UPDATE ITEM SET ITEM_TEXT = %s WHERE ITEM_ID = %s AND POLL_ID = %s"
                        cursor.execute(update_query, (new_text, selected_item.data(Qt.UserRole), self.poll_id))
                        self.parent.connection.commit()
                        print(f"Item ID {selected_item.data(Qt.UserRole)} updated in poll ID {self.poll_id}")

                        # Update UI
                        selected_item.setText(new_text)
                except pymysql.MySQLError as e:
                    print(f"Database error: {e}")

    def delete_item(self):
        selected_item = self.items_list.currentItem()
        if selected_item:
            try:
                with self.parent.connection.cursor() as cursor:
                    # Delete the selected item
                    delete_query = "DELETE FROM ITEM WHERE ITEM_ID = %s AND POLL_ID = %s"
                    cursor.execute(delete_query, (selected_item.data(Qt.UserRole), self.poll_id))
                    self.parent.connection.commit()
                    print(f"Item ID {selected_item.data(Qt.UserRole)} deleted from poll ID {self.poll_id}")

                    # Update UI
                    self.items_list.takeItem(self.items_list.row(selected_item))
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")

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
                    poll_insert_query = """
                    INSERT INTO POLL (START_DATE, END_DATE, QUESTION, ITEMCOUNT, POLLTOTAL, REGDATE, CREATED_BY) 
                    VALUES (%s, %s, %s, 0, 0, %s, %s)
                    """
                    cursor.execute(poll_insert_query, (start_date, end_date, question, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.parent.user_id))
                    self.parent.connection.commit()

                    # Get the ID of the created poll
                    cursor.execute("SELECT LAST_INSERT_ID()")
                    poll_id = cursor.fetchone()['LAST_INSERT_ID()']

                    # Open the AddPollItemsWindow
                    add_items_window = AddPollItemsWindow(self.parent, poll_id)
                    add_items_window.exec_()

                    print(f"Poll created with question: '{question}'")

            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("Please enter start date, end date, and question.")
            
class AddPollItemsWindow(QDialog):
    def __init__(self, parent, poll_id):
        super().__init__()
        self.parent = parent
        self.poll_id = poll_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Poll Items')
        self.layout = QVBoxLayout()

        self.item_label = QLabel('Enter Poll Items (comma separated):')
        self.item_text = QLineEdit(self)
        self.layout.addWidget(self.item_label)
        self.layout.addWidget(self.item_text)

        self.add_items_button = QPushButton('Add Items', self)
        self.add_items_button.clicked.connect(self.add_poll_items)
        self.layout.addWidget(self.add_items_button)

        self.setLayout(self.layout)

    def add_poll_items(self):
        items_text = self.item_text.text()
        items = [item.strip() for item in items_text.split(',') if item.strip()]  # Split items by comma and remove empty strings

        if items:
            try:
                with self.parent.connection.cursor() as cursor:
                    # For each item, determine the next ITEM_ID for the current POLL_ID
                    for item in items:
                        cursor.execute("SELECT MAX(ITEM_ID) as max_id FROM ITEM WHERE POLL_ID = %s", (self.poll_id,))
                        result = cursor.fetchone()
                        next_item_id = 1 if result['max_id'] is None else result['max_id'] + 1

                        # Insert item into ITEM table with the calculated ITEM_ID
                        item_insert_query = "INSERT INTO ITEM (ITEM_ID, POLL_ID, ITEM_TEXT, VOTE_COUNT) VALUES (%s, %s, %s, 0)"
                        cursor.execute(item_insert_query, (next_item_id, self.poll_id, item))

                    # Commit the transaction
                    self.parent.connection.commit()
                    print(f"Items added to poll (ID: {self.poll_id}): {items}")

                    # Close the current window
                    self.close()
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("Please enter poll items.")


class ViewPollsWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('View Polls and Vote')
        self.layout = QVBoxLayout()

        current_datetime = datetime.now()

        try:
            with self.parent.connection.cursor() as cursor:
                # Retrieve all polls
                poll_query = "SELECT * FROM POLL"
                cursor.execute(poll_query)
                polls = cursor.fetchall()

                for poll in polls:
                    poll_id = poll['POLL_ID']
                    question = poll['QUESTION']
                    end_date = datetime.strptime(poll['END_DATE'], '%Y-%m-%d %H:%M:%S')

                    status = " (Active)" if current_datetime < end_date else " (Closed)"
                    poll_button = QPushButton(question + status, self)
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
'''
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
        # Check if the user has already voted in this poll
        if self.has_user_voted(self.poll_id):
            print("You have already voted in this poll.")
            return

        try:
            with self.parent.connection.cursor() as cursor:
                # Update vote count for the specified item
                update_vote_query = "UPDATE ITEM SET VOTE_COUNT = VOTE_COUNT + 1 WHERE ITEM_ID = %s"
                cursor.execute(update_vote_query, (item_id,))

                # Record the user's vote in USER_VOTE table
                record_user_vote_query = "INSERT INTO USER_VOTE (POLL_ID, USER_ID) VALUES (%s, %s)"
                cursor.execute(record_user_vote_query, (self.poll_id, self.parent.user_id))

                # Commit the transaction
                self.parent.connection.commit()
                print(f"Vote recorded for Item ID: {item_id}")

                # Refresh the items in the current window
                self.refresh_items()

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

    def has_user_voted(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                vote_check_query = "SELECT COUNT(*) FROM USER_VOTE WHERE POLL_ID = %s AND USER_ID = %s"
                cursor.execute(vote_check_query, (poll_id, self.parent.user_id))
                result = cursor.fetchone()
                return result['COUNT(*)'] > 0
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            return False
'''
        

class VoteItemWindow(QDialog):
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
        # Check if the user has already voted in this poll
        if self.has_user_voted(self.poll_id):
            QMessageBox.information(self, "Already Voted", "You have already voted in this poll.")
            return

        try:
            with self.parent.connection.cursor() as cursor:
                # Update vote count for the specified item
                update_vote_query = "UPDATE ITEM SET VOTE_COUNT = VOTE_COUNT + 1 WHERE ITEM_ID = %s"
                cursor.execute(update_vote_query, (item_id,))

                # Record the user's vote in USER_VOTE table
                record_user_vote_query = "INSERT INTO USER_VOTE (POLL_ID, USER_ID) VALUES (%s, %s)"
                cursor.execute(record_user_vote_query, (self.poll_id, self.parent.user_id))

                # Commit the transaction
                self.parent.connection.commit()
                print(f"Vote recorded for Item ID: {item_id}")

                # Refresh the items in the current window
                self.refresh_items()

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

    def has_user_voted(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                vote_check_query = "SELECT COUNT(*) FROM USER_VOTE WHERE POLL_ID = %s AND USER_ID = %s"
                cursor.execute(vote_check_query, (poll_id, self.parent.user_id))
                result = cursor.fetchone()
                return result['COUNT(*)'] > 0
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            return False
        
    def refresh_items(self):
        # 현재 표시된 항목들을 제거합니다.
        for i in reversed(range(self.layout.count())): 
            widgetToRemove = self.layout.itemAt(i).widget()
            # 위젯이 있으면 제거합니다.
            if widgetToRemove is not None:
                widgetToRemove.setParent(None)

        # 최신 투표 항목 데이터를 불러옵니다.
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM ITEM WHERE POLL_ID = %s", (self.poll_id,))
                self.items = cursor.fetchall()

                for item in self.items:
                    item_id = item['ITEM_ID']
                    item_text = item['ITEM_TEXT']
                    vote_count = item['VOTE_COUNT']

                    # 갱신된 정보로 버튼을 다시 만듭니다.
                    item_button = QPushButton(f"Item ID: {item_id}, Item Text: {item_text}, Vote Count: {vote_count}", self)
                    item_button.clicked.connect(lambda _, iid=item_id: self.vote_for_item(iid))
                    self.layout.addWidget(item_button)

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")


class LoginScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Seoultech Voting System Login')
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
            
    

class DeletePollWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Delete Poll')
        self.layout = QVBoxLayout()

        self.poll_combo_box = QComboBox(self)
        self.load_polls()
        self.layout.addWidget(self.poll_combo_box)

        self.delete_button = QPushButton('Delete Poll', self)
        self.delete_button.clicked.connect(self.delete_poll)
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

    def load_polls(self):
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT POLL_ID, QUESTION FROM POLL")
                for poll in cursor.fetchall():
                    self.poll_combo_box.addItem(f"{poll['QUESTION']}", poll['POLL_ID'])
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

    def delete_poll(self):
        poll_id = self.poll_combo_box.currentData()
        if self.can_modify_or_delete(poll_id):
            try:
                with self.parent.connection.cursor() as cursor:
                    cursor.execute("DELETE FROM ITEM WHERE POLL_ID = %s", (poll_id,))
                    cursor.execute("DELETE FROM POLL WHERE POLL_ID = %s", (poll_id,))
                    self.parent.connection.commit()
                    print(f"Poll ID {poll_id} deleted successfully")
                    self.poll_combo_box.removeItem(self.poll_combo_box.currentIndex())
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("You do not have permission to delete this poll.")

    def can_modify_or_delete(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT CREATED_BY FROM POLL WHERE POLL_ID = %s", (poll_id,))
                poll = cursor.fetchone()
                return self.parent.user_is_admin or (poll and poll['CREATED_BY'] == self.parent.user_id)
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            return False
        

class ModifyPollWindow(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Modify Poll')
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.poll_combo_box = QComboBox(self)
        self.load_polls()
        form_layout.addRow('Select Poll:', self.poll_combo_box)

        self.start_date_input = QDateTimeEdit(self)
        self.end_date_input = QDateTimeEdit(self)
        self.question_input = QLineEdit(self)

        form_layout.addRow('Start Date:', self.start_date_input)
        form_layout.addRow('End Date:', self.end_date_input)
        form_layout.addRow('Question:', self.question_input)

        self.layout.addLayout(form_layout)

        self.save_changes_button = QPushButton('Save Changes', self)
        self.save_changes_button.clicked.connect(self.save_changes)
        self.manage_items_button = QPushButton('Manage Items', self)
        self.manage_items_button.clicked.connect(self.manage_items)
        
        self.layout.addWidget(self.save_changes_button)
        self.layout.addWidget(self.manage_items_button)

        self.setLayout(self.layout)

    def load_polls(self):
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT POLL_ID, QUESTION FROM POLL")
                for poll in cursor.fetchall():
                    self.poll_combo_box.addItem(f"{poll['QUESTION']}", poll['POLL_ID'])
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")

    def save_changes(self):
        poll_id = self.poll_combo_box.currentData()
        start_date = self.start_date_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        end_date = self.end_date_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        question = self.question_input.text()

        if self.can_modify_or_delete(poll_id):
            try:
                with self.parent.connection.cursor() as cursor:
                    update_query = "UPDATE POLL SET START_DATE = %s, END_DATE = %s, QUESTION = %s WHERE POLL_ID = %s"
                    cursor.execute(update_query, (start_date, end_date, question, poll_id))
                    self.parent.connection.commit()
                    print(f"Poll ID {poll_id} updated successfully")
            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
        else:
            print("You do not have permission to modify this poll.")

    def manage_items(self):
        poll_id = self.poll_combo_box.currentData()
        if self.can_modify_or_delete(poll_id):
            manage_items_window = ManagePollItemsWindow(self.parent, poll_id)
            manage_items_window.exec_()
        else:
            print("You do not have permission to manage items for this poll.")

    def can_modify_or_delete(self, poll_id):
        try:
            with self.parent.connection.cursor() as cursor:
                cursor.execute("SELECT CREATED_BY FROM POLL WHERE POLL_ID = %s", (poll_id,))
                poll = cursor.fetchone()
                return self.parent.user_is_admin or (poll and poll['CREATED_BY'] == self.parent.user_id)
        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            return False

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

        self.view_polls_button = QPushButton('View Polls and Vote', self)
        self.view_polls_button.clicked.connect(self.show_view_polls)
        self.layout.addWidget(self.view_polls_button)

        # 변경: Vote 버튼을 Quit 버튼으로 변경하고, 클릭 시 프로그램 종료
        self.quit_button = QPushButton('Quit', self)
        self.quit_button.clicked.connect(self.quit_program)
        self.layout.addWidget(self.quit_button)
        
        self.modify_poll_button = QPushButton('Modify Poll', self)
        self.modify_poll_button.clicked.connect(self.show_modify_poll)
        self.layout.addWidget(self.modify_poll_button)

        self.delete_poll_button = QPushButton('Delete Poll', self)
        self.delete_poll_button.clicked.connect(self.show_delete_poll)
        self.layout.addWidget(self.delete_poll_button)


        self.setLayout(self.layout)

    def show_create_poll(self):
        create_poll_window = CreatePollWindow(self.parent)
        create_poll_window.exec_()

    def show_view_polls(self):
        view_polls_window = ViewPollsWindow(self.parent)
        view_polls_window.exec_()

    def show_modify_poll(self):
        modify_poll_window = ModifyPollWindow(self.parent)
        modify_poll_window.exec_()

    def show_delete_poll(self):
        delete_poll_window = DeletePollWindow(self.parent)
        delete_poll_window.exec_()

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
        
        # 로깅 설정
        logging.basicConfig(filename='log.txt', level=logging.INFO, 
                            format='%(asctime)s:%(levelname)s:%(message)s')

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
        
        # Initialize user admin status
        self.user_is_admin = False
        
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
                    
                # ... existing code ...
                cursor.execute("SHOW TABLES LIKE 'USER_VOTE'")
                if not cursor.fetchone():
                    self.create_user_vote_table(cursor)
                # Commit the transaction

                # Commit the transaction
                self.connection.commit()

        except pymysql.MySQLError as e:
            print(f"Database error: {e}")
            
    def create_user_vote_table(self, cursor):
        query = '''
        CREATE TABLE USER_VOTE (
            VOTE_ID int(11) NOT NULL AUTO_INCREMENT,
            POLL_ID int(11) NOT NULL,
            USER_ID int(11) NOT NULL,
            PRIMARY KEY (VOTE_ID),
            FOREIGN KEY (POLL_ID) REFERENCES POLL(POLL_ID),
            FOREIGN KEY (USER_ID) REFERENCES ACCOUNT(ACCOUNT_ID)
        ) AUTO_INCREMENT=1
        '''
        cursor.execute(query)
        
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
            CREATED_BY int(11),  # Adding the CREATED_BY column
            PRIMARY KEY(POLL_ID),
            FOREIGN KEY (CREATED_BY) REFERENCES ACCOUNT(ACCOUNT_ID)  # Setting up a foreign key reference
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
            IS_ADMIN tinyint(1) NOT NULL DEFAULT '0',  # New field for admin status
            PRIMARY KEY(ACCOUNT_ID)
        ) AUTO_INCREMENT=1
        '''
        cursor.execute(query)


    def init_ui(self):
        self.setWindowTitle('Seoultech Voting System')

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
                            self.user_is_admin = existing_user['IS_ADMIN'] == 1  # Set user admin status
                            print(f"Login successful for user '{username}'")

                            # Remove the login screen and show the main menu
                            self.layout.removeWidget(self.login_screen)
                            self.layout.addWidget(self.main_menu)
                            self.login_screen.deleteLater()

                            # Show login result on the login screen
                            self.login_screen.show_login_result(True)
                            
                            logging.info(f"Login successful for user '{username}'")
                            if existing_user['IS_ADMIN'] == 1:
                                logging.info(f"Admin login successful for user '{username}'")
                            else:
                                logging.info(f"User login successful for user '{username}'")
                        else:
                            print(f"Login failed for user '{username}': Incorrect password")
                            # Show login result on the login screen
                            self.login_screen.show_login_result(False)
                            logging.info(f"Login failed for user '{username}': Incorrect password")
                            
                        if existing_user['IS_ADMIN'] == 1:
                            print(f"Admin login successful for user '{username}'")
                        else:
                            print(f"User login successful for user '{username}'")
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
                        
                        logging.info(f"New account created and logged in for user '{username}'")

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
                        
                        logging.info(f"Vote recorded for '{item_text}' in poll '{item_text}'")
                    else:
                        print(f"Poll '{item_text}' not found.")
                        logging.info(f"Poll '{item_text}' not found.")

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

