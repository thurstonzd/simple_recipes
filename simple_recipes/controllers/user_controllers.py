import os

from flask import render_template, redirect, url_for, flash

import flask_login

import scrypt

from simple_recipes import app, login_manager
from simple_recipes.db.users import *
from simple_recipes.forms import UserForm

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_name):
    d = get_user(user_name=user_name)
    if not d: return

    user = User()
    user.id = user_name
    return user

@login_manager.request_loader
def request_loader(request):
    if not request.form: return
    user_name = request.form.get('user_name')
    entered_password = request.form.get('user_pw')

    if user_name and entered_password and get_user(user_name=user_name):
        user = User()
        user.id = user_name
        if is_user_password_valid(user_name, entered_password):
            user.is_authenticated = True
        else: flash("Incorrect Password")

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = UserForm()

    form.user_name.required = True
    form.current_pw.required = True

    if form.validate_on_submit():
        user_name = form.user_name.data
        user_pw = form.current_pw.data

        try:
            if is_user_password_valid(user_name, user_pw):
                user = User()
                user.id = user_name
                flask_login.login_user(user)

                return redirect(url_for('account'))
            else:
                flash("Incorrect username or password")
        except PermissionError as exc:
            flash(exc)

    return render_template('users/login.html', form=form)

@app.route('/logout/')
def logout():
    flask_login.logout_user()
    flash("Logged out successfully")
    return redirect(url_for('login'))

@app.route('/account/', methods=['GET', 'POST'])
@flask_login.login_required
def account():
    user_name = flask_login.current_user.id
    user_data = get_user(user_name=user_name)
    if user_data['user_status'] == RESET:
        flash(  "Your account has been reset. "
                "You might want to go ahead and change your password.")
        change_user_status(user_name=user_name)
    return render_template('users/account.html')
        
@app.route('/account/change_password/', methods=['GET', 'POST'])
@flask_login.login_required
def change_password():
    form = UserForm()
    user_name = flask_login.current_user.id
    current_pw = form.current_pw.data

    form.current_pw.required = True
    form.new_pw.required = True
    form.new_pw_confirmation.required = True

    if form.validate_on_submit():
        if form.new_pw.data != form.new_pw_confirmation.data:
            flash("New password must match in both fields!")
        if is_user_password_valid(user_name, current_pw):
            salt = os.urandom(64)
            hashed = scrypt.hash(form.new_pw.data, salt)
            update_user_password(user_name, hashed, salt)
            flash("Password successfully changed")
            return redirect(url_for('account'))

    return render_template('users/change_password.html', form=form)