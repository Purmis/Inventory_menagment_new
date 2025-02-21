import os
import secrets

class Config:
    # Bazowa ścieżka aplikacji
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Katalog na dane
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Ścieżki do baz danych
    PRODUCTS_DB_PATH = os.path.join(DATA_DIR, 'products.db')
    USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')
    
    # Stałe lokalizacje
    LOCATIONS = [
        "Panorama M&M GOLD",
        "Panorama VVS",
        "MODO M&M GOLD",
        "Galeria Północna M&M GOLD",
        "Klif M&M GOLD",
        "Stary Browar M&M GOLD"
    ]
    
    # Ścieżka do bazy danych
    DB_PATH = os.path.join(BASE_DIR, 'inventory.db')
    
    # Katalog na przesyłane pliki (upewniamy się, że ścieżka jest poprawna)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'img')
    
    # Dozwolone rozszerzenia plików
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Bezpieczny klucz wygenerowany przy pomocy secrets
    SECRET_KEY = 'ff41d4f39d6dd7668716f55112f756e5b01087b94b554156c7c80e25227e4500'
    
    # Ustawienia sesji
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minut w sekundach
    SESSION_REFRESH_EACH_REQUEST = True
