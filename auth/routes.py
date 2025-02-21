from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta
from .models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and User.verify_password(username, password):
            # Ustaw sesję jako nietrwałą (wygaśnie po zamknięciu przeglądarki)
            session.permanent = False
            login_user(user)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Nieprawidłowa nazwa użytkownika lub hasło', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@login_required
def user_list():
    if not current_user.is_admin:
        flash('Brak dostępu - wymagane uprawnienia administratora', 'error')
        return redirect(url_for('index'))
    
    users = User.get_all_users()
    return render_template('auth/user_list.html', users=users)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def user_add():
    if not current_user.is_admin:
        flash('Brak dostępu - wymagane uprawnienia administratora', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.get_by_username(username):
            flash('Użytkownik o takiej nazwie już istnieje', 'error')
        else:
            if User.create(username, password, is_admin):
                flash(f'Użytkownik {username} został utworzony', 'success')
                return redirect(url_for('auth.user_list'))
            else:
                flash('Błąd podczas tworzenia użytkownika', 'error')
    
    return render_template('auth/user_form.html', User=User)

@auth_bp.route('/users/delete/<username>')
@login_required
def user_delete(username):
    if not current_user.is_admin:
        flash('Brak dostępu - wymagane uprawnienia administratora', 'error')
        return redirect(url_for('index'))
    
    if username == 'admin' or username == current_user.username:
        flash('Nie można usunąć tego użytkownika', 'error')
    else:
        if User.delete(username):
            flash(f'Użytkownik {username} został usunięty', 'success')
        else:
            flash('Błąd podczas usuwania użytkownika', 'error')
    
    return redirect(url_for('auth.user_list'))
