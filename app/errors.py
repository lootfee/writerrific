from flask import render_template
from app import app, db
from app.forms import LoginForm, RegistrationForm

@app.errorhandler(404)
def not_found_error(error):
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('home'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('home'))
	return render_template('404.html', register_form=register_form, login_form=login_form), 404
	
@app.errorhandler(413)
def file_too_large_error(error):
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('home'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('home'))
	db.session.rollback()
	return render_template('413.html', register_form=register_form, login_form=login_form), 413

@app.errorhandler(500)
def internal_error(error):
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('home'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('home'))
	db.session.rollback()
	return render_template('500.html', register_form=register_form, login_form=login_form), 500