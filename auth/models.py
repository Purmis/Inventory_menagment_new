from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from config import Config

def init_auth_db():
    print("Inicjalizacja bazy danych użytkowników...")
    conn = sqlite3.connect(Config.USERS_DB_PATH)
    c = conn.cursor()
    
    # Upewnij się, że stara tabela zostanie usunięta
    c.execute('DROP TABLE IF EXISTS users')
    
    # Utwórz nową tabelę z poprawną strukturą
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT DEFAULT '',
        position TEXT DEFAULT '',
        location TEXT DEFAULT '',
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()
    print("Inicjalizacja bazy danych użytkowników zakończona.")

class User:
    def __init__(self, username, full_name="", position="", location="", is_admin=False):
        self.username = username.upper()
        self.full_name = full_name
        self.position = position
        self.location = location
        self.is_admin = is_admin
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        
    def is_manager(self):
        return self.location == "OBRÓT WŁASNY" and not self.is_admin

    def get_id(self):
        return self.username

    @staticmethod
    def create(username, password, full_name="", position="", location="", is_admin=False):
        conn = User._get_db()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO users 
                        (username, password_hash, full_name, position, location, is_admin) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     [username.upper(), generate_password_hash(password), 
                      full_name, position, location, is_admin])
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_username(username):
        conn = User._get_db()
        c = conn.cursor()
        try:
            # Precyzyjnie określamy kolejność kolumn
            user = c.execute('''
                SELECT 
                    username,
                    password_hash,
                    full_name,
                    position,
                    location,
                    is_admin 
                FROM users 
                WHERE UPPER(username) = UPPER(?)
            ''', [username]).fetchone()
            
            if user:
                return User(
                    username=user[0],
                    full_name=user[2],
                    position=user[3],
                    location=user[4],
                    is_admin=user[5]
                )
            return None
        finally:
            conn.close()

    @staticmethod
    def verify_password(username, password):
        conn = User._get_db()
        c = conn.cursor()
        try:
            user = c.execute('SELECT password_hash FROM users WHERE UPPER(username) = UPPER(?)',
                           [username]).fetchone()
            if user and check_password_hash(user[0], password):
                return True
            return False
        finally:
            conn.close()

    @staticmethod
    def get_all_users():
        conn = User._get_db()
        c = conn.cursor()
        users = c.execute('SELECT username, full_name, position, location, is_admin FROM users').fetchall()
        conn.close()
        return [{
            'username': user[0].upper(),
            'full_name': user[1],
            'position': user[2],
            'location': user[3],
            'is_admin': user[4],
            'is_active': True
        } for user in users]

    @staticmethod
    def delete(username):
        conn = User._get_db()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM users WHERE username = ? AND username != "admin"', [username])
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_locations():
        return Config.LOCATIONS

    @staticmethod
    def _get_db():
        return sqlite3.connect(Config.USERS_DB_PATH)
