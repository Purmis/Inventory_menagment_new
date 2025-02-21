from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import sqlite3
from database import get_db_connection, init_db
from config import Config
from PIL import Image
from contextlib import closing
from flask_login import LoginManager, login_required, current_user
from auth.models import User, init_auth_db
from auth.routes import auth_bp
from healthz import healthz_bp

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Konfiguracja sesji
app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
app.config['SESSION_REFRESH_EACH_REQUEST'] = Config.SESSION_REFRESH_EACH_REQUEST

# Konfiguracja
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

# Konfiguracja Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Zaloguj się, aby uzyskać dostęp.'

@login_manager.user_loader
def load_user(username):
    return User.get_by_username(username)

# Rejestracja blueprintu autoryzacji
app.register_blueprint(auth_bp)

# Rejestracja blueprintu health check
app.register_blueprint(healthz_bp)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect(Config.PRODUCTS_DB_PATH)  # Zmiana na nową ścieżkę
    db.row_factory = sqlite3.Row
    return db

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transfers')
def transfers():
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    
    db = get_db()
    query = "SELECT * FROM produkty WHERE 1=1"
    params = []
    
    if search:
        query += " AND (produkt_id LIKE ? OR nazwa LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    if location:
        query += " AND lokalizacja = ?"
        params.append(location)
    
    products = db.execute(query, params).fetchall()
    locations = db.execute("SELECT DISTINCT lokalizacja FROM produkty").fetchall()
    
    return render_template('transfers.html', 
                         products=products,
                         locations=[loc[0] for loc in locations])

@app.route('/transfer_product', methods=['POST'])
def transfer_product():
    product_id = request.form.get('product_id')
    new_location = request.form.get('new_location')
    
    if not all([product_id, new_location]):
        flash('Nieprawidłowe dane', 'error')
        return redirect(url_for('transfers'))
    
    try:
        db = get_db()
        db.execute('UPDATE produkty SET lokalizacja = ? WHERE produkt_id = ?',
                  [new_location, product_id])
        db.commit()
        flash(f'Produkt został przeniesiony do {new_location}', 'success')
    except Exception as e:
        flash(f'Błąd podczas przenoszenia: {str(e)}', 'error')
    
    return redirect(url_for('transfers'))

@app.route('/products')
def product_list():
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    
    db = get_db()
    query = "SELECT * FROM produkty WHERE 1=1"
    params = []
    
    if search:
        query += " AND (produkt_id LIKE ? OR nazwa LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    if location:
        query += " AND lokalizacja = ?"
        params.append(location)
    
    products = db.execute(query, params).fetchall()
    
    # Używamy lokalizacji z konfiguracji zamiast z bazy danych
    return render_template('product_list.html', 
                         products=products,
                         locations=Config.LOCATIONS)

@app.route('/product/add', methods=['GET', 'POST'])
def product_add():
    if request.method == 'POST':
        try:
            # Sprawdzenie wymaganych pól
            required_fields = ['produkt_id', 'nazwa', 'kolekcja', 'kategoria', 'masa_calkowita', 'cena', 'kolor_zlota', 'lokalizacja']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Pole {field} jest wymagane', 'error')
                    return render_template('product_form.html', product=None)

            # Przygotowanie danych
            data = {
                'produkt_id': request.form['produkt_id'],
                'nazwa': request.form['nazwa'],
                'kolekcja': request.form['kolekcja'],
                'kategoria': request.form['kategoria'],
                'masa_calkowita': float(request.form['masa_calkowita']),
                'cena': float(request.form['cena']),
                'kolor_zlota': request.form['kolor_zlota'],
                'rozmiar': request.form.get('rozmiar', ''),
                'lokalizacja': request.form['lokalizacja'],
                'ma_diamenty': 'ma_diamenty' in request.form,
                'masa_diamentu': float(request.form.get('masa_diamentu') or 0),
                'kolor': request.form.get('kolor'),
                'czystosc': request.form.get('czystosc'),
                'szlif': request.form.get('szlif'),
                'kamienie_dodatkowe': int(request.form.get('kamienie_dodatkowe') or 0),
                'kolor_kamieni': request.form.get('kolor_kamieni'),
                'jakosc_kamieni': request.form.get('jakosc_kamieni'),
                'ma_inne_kamienie': 'ma_inne_kamienie' in request.form,
                'nazwa_kamienia': request.form.get('nazwa_kamienia'),
                'wielkosc_kamienia': float(request.form.get('wielkosc_kamienia') or 0)
            }

            # Obsługa zdjęć
            if 'product_image' in request.files:
                product_image = request.files['product_image']
                if product_image and allowed_file(product_image.filename):
                    data['product_image_path'] = save_product_image(product_image, data['produkt_id'], 'product')

            if 'cert_image' in request.files:
                cert_image = request.files['cert_image']
                if cert_image and allowed_file(cert_image.filename):
                    data['cert_image_path'] = save_product_image(cert_image, data['produkt_id'], 'cert')

            # Zapisywanie do bazy danych
            with closing(get_db()) as db:
                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' * len(data))
                query = f'INSERT INTO produkty ({columns}) VALUES ({placeholders})'
                
                db.execute(query, list(data.values()))
                db.commit()

            flash('Produkt został dodany pomyślnie', 'success')
            return redirect(url_for('product_list'))  # Przekierowanie do listy produktów

        except ValueError as e:
            flash(f'Błąd walidacji danych: {str(e)}', 'error')
            return render_template('product_form.html', product=None)
        except sqlite3.IntegrityError:
            flash('Produkt o podanym ID już istnieje', 'error')
            return render_template('product_form.html', product=None)
        except Exception as e:
            app.logger.error(f'Błąd podczas dodawania produktu: {str(e)}')
            flash('Wystąpił błąd podczas dodawania produktu', 'error')
            return render_template('product_form.html', product=None, Config=Config)

    return render_template('product_form.html', product=None, Config=Config)

@app.route('/product/<product_id>')
def product_view(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM produkty WHERE produkt_id = ?', 
                        [product_id]).fetchone()
    if product is None:
        flash('Produkt nie został znaleziony', 'error')
        return redirect(url_for('product_list'))
    
    # Konwertujemy ścieżki na format URL
    if product['product_image_path']:
        product = dict(product)
        product['product_image_path'] = product['product_image_path'].replace('\\', '/')
    if product['cert_image_path']:
        product['cert_image_path'] = product['cert_image_path'].replace('\\', '/')
    
    return render_template('product_view.html', product=product)

@app.route('/product/<product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM produkty WHERE produkt_id = ?', 
                        [product_id]).fetchone()
    if product is None:
        flash('Produkt nie został znaleziony', 'error')
        return redirect(url_for('product_list'))
    
    if request.method == 'POST':
        # Tu dodaj logikę aktualizacji produktu
        flash('Produkt został zaktualizowany', 'success')
        return redirect(url_for('product_view', product_id=product_id))
    
    return render_template('product_form.html', product=product)

@app.route('/product/<product_id>/delete')
def product_delete(product_id):
    db = get_db()
    db.execute('DELETE FROM produkty WHERE produkt_id = ?', [product_id])
    db.commit()
    flash('Produkt został usunięty', 'success')
    return redirect(url_for('product_list'))

def save_product_image(file, product_id, image_type):
    if not file or not allowed_file(file.filename):
        return None

    try:
        # Bezpieczna nazwa pliku
        filename = f"{image_type}.jpg"
        relative_path = os.path.join('img', str(product_id))
        absolute_path = os.path.join(app.static_folder, relative_path)
        
        # Tworzenie katalogu jeśli nie istnieje
        os.makedirs(absolute_path, exist_ok=True)
        
        filepath = os.path.join(absolute_path, filename)
        
        # Zapisywanie i przetwarzanie obrazu
        with Image.open(file) as img:
            img = img.convert('RGB')
            img.thumbnail((800, 800))
            img.save(filepath, "JPEG", quality=85)
        
        return relative_path.replace('\\', '/') + '/' + filename

    except Exception as e:
        app.logger.error(f"Błąd podczas zapisywania zdjęcia: {str(e)}")
        return None

# Przed require_login()
@app.before_request
def require_login():
    # Nie wymagamy logowania dla statycznych plików i endpointu logowania
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint == 'auth.login')):
        return
    
    # Wymagaj logowania dla wszystkich innych endpointów
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # Upewniamy się, że katalogi istnieją
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)  # Utworzenie katalogu data
    
    # Inicjalizacja bazy danych produktów
    with app.app_context():
        init_db()  # Usuwamy usuwanie bazy, pozwalamy init_db() zdecydować
    
    # Inicjalizacja bazy danych użytkowników tylko jeśli nie istnieje
    if not os.path.exists(Config.USERS_DB_PATH):
        init_auth_db()
        # Utworzenie domyślnego konta administratora
        User.create(
            username='admin',
            password='admin123',
            full_name='Administrator',
            position='Administrator',
            location='WSZYSTKIE',
            is_admin=True
        )
    
    app.run(debug=True, port=5000)
