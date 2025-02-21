import os
from config import Config

def check_files():
    print("Sprawdzanie struktury katalogów i plików...")
    
    # Sprawdź czy istnieje katalog static/img
    if not os.path.exists(Config.UPLOAD_FOLDER):
        print(f"Tworzenie katalogu {Config.UPLOAD_FOLDER}")
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Sprawdź zawartość katalogu img
    print("\nZawartość katalogu static/img:")
    try:
        img_contents = os.listdir(Config.UPLOAD_FOLDER)
        if img_contents:
            for item in img_contents:
                full_path = os.path.join(Config.UPLOAD_FOLDER, item)
                print(f"- {item} ({'katalog' if os.path.isdir(full_path) else 'plik'})")
                
                # Jeśli to katalog produktu, sprawdź jego zawartość
                if os.path.isdir(full_path):
                    product_contents = os.listdir(full_path)
                    for prod_item in product_contents:
                        print(f"  └── {prod_item}")
        else:
            print("(pusty)")
    except Exception as e:
        print(f"Błąd podczas listowania katalogu: {e}")

    # Test zapisu pliku
    print("\nTest zapisu pliku:")
    test_file = os.path.join(Config.UPLOAD_FOLDER, 'test.txt')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        print("✓ Zapis pliku działa poprawnie")
        os.remove(test_file)
        print("✓ Usuwanie pliku działa poprawnie")
    except Exception as e:
        print(f"✗ Problem z zapisem pliku: {e}")

    # Sprawdź ścieżki w bazie danych
    print("\nSprawdzanie ścieżek w bazie danych:")
    import sqlite3
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        products = cur.execute("SELECT produkt_id, product_image_path, cert_image_path FROM produkty").fetchall()
        
        for product in products:
            print(f"\nProdukt {product['produkt_id']}:")
            if product['product_image_path']:
                full_path = os.path.join(Config.BASE_DIR, 'static', product['product_image_path'])
                exists = os.path.exists(full_path)
                print(f"- Zdjęcie produktu: {'✓' if exists else '✗'} {product['product_image_path']}")
                if not exists:
                    print(f"  Pełna ścieżka: {full_path}")
            
            if product['cert_image_path']:
                full_path = os.path.join(Config.BASE_DIR, 'static', product['cert_image_path'])
                exists = os.path.exists(full_path)
                print(f"- Zdjęcie certyfikatu: {'✓' if exists else '✗'} {product['cert_image_path']}")
                if not exists:
                    print(f"  Pełna ścieżka: {full_path}")
                    
        conn.close()
    except Exception as e:
        print(f"Błąd podczas sprawdzania bazy danych: {e}")

if __name__ == "__main__":
    check_files()
