import sqlite3
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.PRODUCTS_DB_PATH)  # Zmiana na nową ścieżkę
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Inicjalizacja bazy danych produktów...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # Upewnij się, że stara tabela zostanie usunięta
    c.execute('DROP TABLE IF EXISTS produkty')
    
    # Utwórz nową tabelę
    c.execute('''CREATE TABLE produkty (
        id INTEGER PRIMARY KEY,
        kolekcja TEXT,
        kategoria TEXT,
        nazwa TEXT,
        produkt_id TEXT UNIQUE,
        masa_calkowita REAL,
        cena REAL,
        kolor_zlota TEXT,
        ma_diamenty BOOLEAN,
        masa_diamentu REAL,
        czystosc TEXT,
        kolor TEXT,
        szlif TEXT,
        kamienie_dodatkowe INTEGER,
        kolor_kamieni TEXT,
        jakosc_kamieni TEXT,
        ma_inne_kamienie BOOLEAN,
        nazwa_kamienia TEXT,
        wielkosc_kamienia REAL,
        rozmiar TEXT,
        lokalizacja TEXT,
        product_image_path TEXT,
        cert_image_path TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("Inicjalizacja bazy danych produktów zakończona.")
