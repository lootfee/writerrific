from flask import render_template, flash, redirect, url_for, request, current_app, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db, photos
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, CreateProjectForm, EditProjectForm, CreateChapterForm, EditChapterForm, CommentForm, PublishForm, ReviewForm, CommentReviewForm
from app.models import User, Project, Comment, Chapter, Genre, Rating
from datetime import datetime, timedelta
from app.email import send_password_reset_email
import markdown2 
import requests
from werkzeug.urls import url_parse


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
	
@app.route('/sw.js', methods=['GET'])
def sw():
    return app.send_static_file('sw.js')	

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
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
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			user.set_password(register_form.register_password.data)
			db.session.add(user)
			db.session.commit()
			flash('Thank you for registering')
			return redirect(url_for('home'))
	return render_template('home.html', title='Home', register_form=register_form, login_form=login_form)


@app.route('/explore', methods=['GET', 'POST'])
def index():
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('index'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('index'))
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			user.set_password(register_form.register_password.data)
			db.session.add(user)
			db.session.commit()
			flash('Thank you for registering')
			return redirect(url_for('index'))
	form = CreateProjectForm()
	if form.validate_on_submit():
		genres = form.genre.data
		genre_list = genres.split(',')
		proj = Project(title=form.title.data, synopsis=form.synopsis.data, user_id=current_user.id)
		if form.cover_pic.data:
			cover_pic_filename = photos.save(form.cover_pic.data)
			proj.cover_pic = photos.url(cover_pic_filename)
		if form.cover_pic_credit.data:
			proj.cover_pic_credit = form.cover_pic_credit.data
		db.session.add(proj)
		db.session.commit()
		for g in genre_list:
			g_query = Genre.query.filter_by(name=g).first()
			if g_query is None:
				gname = Genre(name=g)
				db.session.add(gname)
				proj.genre.append(gname)
				db.session.commit()
			else:
				proj.genre.append(g_query)
				db.session.commit()
		return redirect(url_for('project', id=proj.id, title=proj.title))
	page = request.args.get('page', 1, type=int)
	projects = Project.query.order_by(Project.date_published.desc()).filter(Project.date_published.isnot(None)).filter_by(date_quarantined=None).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=projects.next_num) \
		if projects.has_next else None
	prev_url = url_for('index', page=projects.prev_num) \
		if projects.has_prev else None
	return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url, form=form, register_form=register_form, login_form=login_form)
	
@app.route('/advice', methods=['GET', 'POST'])
def advice():
	page = request.args.get('page', 1, type=int)
	for_advice_projects = Project.query.order_by(Project.date_seek_review.desc()).filter(Project.date_seek_review.isnot(None)).filter_by(date_published=None, date_quarantined=None).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=projects.next_num) \
		if for_advice_projects.has_next else None
	prev_url = url_for('index', page=projects.prev_num) \
		if for_advice_projects.has_prev else None
	#last_date_submitted = for_advice_projects.chapters.order_by(Chapter.date_submitted.desc()).first().date_submitted
	return render_template('index.html', title='Give advice', for_advice_projects=for_advice_projects.items, next_url=next_url, prev_url=prev_url)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('index'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.login_email.data).first()
		if user is None or not user.check_password(form.login_password.data):
			flash('Invalid email or password')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
	return render_template('login.html', title='Sign In', form=form, register_form=register_form, login_form=login_form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))	
	
@app.route('/privacy_policy')
def privacy_policy():
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('privacy_policy'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('privacy_policy'))
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			user.set_password(register_form.register_password.data)
			db.session.add(user)
			db.session.commit()
			flash('Thank you for registering')
			return redirect(url_for('privacy_policy'))
	return render_template('privacy_policy.html', title='Privacy Policy', register_form=register_form, login_form=login_form)
	
@app.route('/terms_of_service')
def terms_of_service():
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('terms_of_service'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('index'))
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			user.set_password(register_form.register_password.data)
			db.session.add(user)
			db.session.commit()
			flash('Thank you for registering')
			return redirect(url_for('terms_of_service'))
	return render_template('terms_of_service.html', title='Terms of Service', register_form=register_form, login_form=login_form)
	
@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('index'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.register_username.data, email=form.register_email.data)
		user.set_password(form.register_password.data)
		db.session.add(user)
		db.session.commit()
		flash('Thank you for registering')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form, register_form=register_form, login_form=login_form)
	
@app.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			loginuser = User.query.filter_by(email=login_form.login_email.data).first()
			if loginuser is None or not loginuser.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				current_page = request.url
				if not current_page or url_parse(current_page).netloc != '':
					next_page = url_for('index')
				return redirect(current_page)
			login_user(loginuser, remember=login_form.remember_me.data)
			current_page = request.url
			if not current_page or url_parse(current_page).netloc != '':
				next_page = url_for('index')
			return redirect(current_page)
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			register_user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			register_user.set_password(register_form.register_password.data)
			db.session.add(register_user)
			db.session.commit()
			flash('Thank you for registering')
			current_page = request.url
			if not current_page or url_parse(current_page).netloc != '':
				next_page = url_for('index')
			return redirect(current_page)
	user = User.query.filter_by(username=username).first_or_404()
	portfolio = Project.query.filter_by(user_id=user.id, date_quarantined=None).order_by(Project.date_published.desc()).all()
	for p in portfolio:
		pg_list = []
		for pg in p.genre:
			pg_list.append(pg.name)
		p.pg_name = ','.join(pg_list)
	library = user.books.filter_by(date_quarantined=None).order_by(Project.date_published.desc()).all()
	form = CreateProjectForm()
	form2 = EditProjectForm()
	if form.submit.data:
		if form.validate_on_submit():
			genres = form.genre.data
			genre_list = genres.split(',')
			proj = Project(title=form.title.data, synopsis=form.synopsis.data, user_id=current_user.id)
			if form.cover_pic.data:
				cover_pic_filename = photos.save(form.cover_pic.data)
				proj.cover_pic = photos.url(cover_pic_filename)
			elif form.cover_pic_link.data:
				proj.cover_pic_link = form.cover_pic_link.data
			if form.cover_pic_credit.data:
				proj.cover_pic_credit = form.cover_pic_credit.data
			db.session.add(proj)
			db.session.commit()
			for g in genre_list:
				g_query = Genre.query.filter_by(name=g).first()
				if g_query is None:
					gname = Genre(name=g)
					db.session.add(gname)
					proj.genre.append(gname)
					db.session.commit()
				else:
					proj.genre.append(g_query)
					db.session.commit()
			return redirect(url_for('project', id=proj.id, title=proj.title))
	elif form2.edit_submit.data:
		if form2.validate_on_submit():
			edit_proj = Project.query.filter_by(id=form2.proj_id.data).first()
			edit_proj.title = form2.edit_title.data
			edit_proj.synopsis = form2.edit_synopsis.data
			print(form2.edit_cover_pic.data)
			if form2.edit_cover_pic.data:
				edit_cover_pic_filename = photos.save(form2.edit_cover_pic.data)
				edit_proj.cover_pic = photos.url(edit_cover_pic_filename)
				print(form2.edit_cover_pic.data)
			elif form2.edit_cover_pic_link.data:
				edit_proj.cover_pic_link = form2.edit_cover_pic_link.data
				print('form2')
			edit_proj.cover_pic_credit = form2.edit_cover_pic_credit.data
			db.session.commit()
			edit_genres = form2.edit_genre.data
			edit_genre_list = edit_genres.split(',')
			for g in edit_genre_list:
				g_query = Genre.query.filter_by(name=g).first()
				if g_query is None:
					gname = Genre(name=g)
					db.session.add(gname)
					edit_proj.genre.append(gname)
					db.session.commit()
				elif not edit_proj.is_genre(g_query):
					edit_proj.genre.append(g_query)
					db.session.commit()
			return redirect(url_for('project', id=edit_proj.id, title=edit_proj.title))
	'''elif request.method == 'GET':
		for p in portfolio:
			form2.proj_id.data = p.id
			form2.edit_title.data = p.title
			pg_list = []
			for pg in p.genre:
				pg_list.append(pg.name)
			p.pg_name = ','.join(pg_list)
			form2.edit_genre.data = p.pg_name
			form2.edit_synopsis.data = p.synopsis'''
	return render_template('user.html', user=user, title='User', description=user.about_me, form=form, form2=form2, portfolio=portfolio, library=library, register_form=register_form, login_form=login_form)
	
	
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username, current_user.email)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		current_user.email = form.email.data
		if form.profile_pic.data:
			profile_pic_filename = photos.save(form.profile_pic.data)
			current_user.profile_pic = photos.url(profile_pic_filename)
		db.session.commit()
		flash('Your changes have been saved.')
		return redirect(url_for('user', username=current_user.username))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
		form.email.data = current_user.email
	return render_template('edit_profile.html', title='Edit Profile', form=form)
	

						   
@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))
	
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('privacy_policy'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('privacy_policy'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('You will receive an email on how to reset your password if the email that you entered is registered.')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html', title='Reset Password', form=form, register_form=register_form, login_form=login_form)
	
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	user = User.verify_reset_password_token(token)
	if not user:
		return redirect(url_for('index'))
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			user = User.query.filter_by(email=login_form.login_email.data).first()
			if user is None or not user.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				return redirect(url_for('privacy_policy'))
			login_user(user, remember=login_form.remember_me.data)
			return redirect(url_for('privacy_policy'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Your password has been reset.')
		return redirect(url_for('login'))
	return render_template('reset_password.html', form=form, register_form=register_form, login_form=login_form)
	
@app.route('/stories/<id>/<title>', methods=['GET', 'POST'])
def project(id, title):
	register_form = RegistrationForm()
	login_form = LoginForm()
	if login_form.login_submit.data:
		if login_form.validate_on_submit():
			loginuser = User.query.filter_by(email=login_form.login_email.data).first()
			if loginuser is None or not loginuser.check_password(login_form.login_password.data):
				flash('Invalid email or password')
				current_page = request.url
				if not current_page or url_parse(current_page).netloc != '':
					next_page = url_for('index')
				return redirect(current_page)
			login_user(loginuser, remember=login_form.remember_me.data)
			current_page = request.url
			if not current_page or url_parse(current_page).netloc != '':
				next_page = url_for('index')
			return redirect(current_page)
	elif register_form.register_submit.data:
		if register_form.validate_on_submit():
			register_user = User(username=register_form.register_username.data, email=register_form.register_email.data)
			register_user.set_password(register_form.register_password.data)
			db.session.add(register_user)
			db.session.commit()
			flash('Thank you for registering')
			current_page = request.url
			if not current_page or url_parse(current_page).netloc != '':
				next_page = url_for('index')
			return redirect(current_page)
	project = Project.query.filter_by(id=id).first()
	if project.cover_pic_credit:
		project.cover_pic_cred = markdown2.markdown(project.cover_pic_credit)
	chapters = Chapter.query.filter_by(project_id=project.id).order_by(Chapter.chapter_no.asc()).all()
	form = CreateChapterForm()
	if form.submit_chapter.data and form.validate_on_submit():
		chapter = Chapter(chapter_no=form.chapter_number.data, chapter_title=form.chapter_title.data, project_id=project.id, author_id=current_user.id)
		db.session.add(chapter)
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	for c in chapters:
		if c.chapter_body is not None:
			if c.date_submitted < datetime(2018, 12, 31):
				c.body = markdown2.markdown(c.chapter_body)
			else:
				c.body = c.chapter_body
	form1 = CommentReviewForm()
	if form1.post_for_advice.data and form1.validate_on_submit():
		project.date_seek_review = datetime.utcnow()
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	form2 = PublishForm()
	if form2.publish_project.data and form2.validate_on_submit():
		project.date_published = datetime.utcnow()
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	form3 = ReviewForm()
	if form3.submit_review.data and form3.validate_on_submit():
		ratings = Rating(review=form3.review.data, score=form3.score.data, project_id=project.id, user_id=current_user.id)
		db.session.add(ratings)
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	genre = []
	for p in project.genre:
		genre.append(p.name)
	keywords = (', '.join(genre))
	return render_template('project.html', title=project.title, keywords=keywords, description=project.synopsis, project=project, form=form, form1=form1, form2=form2, form3=form3, chapters=chapters, register_form=register_form, login_form=login_form)
	
@app.route('/synopsis/<id>/<title>', methods=['GET', 'POST'])
def project_synopsis(id, title):
	project = Project.query.filter_by(id=id).first()
	#user = User.query.filter_by(username=current_user.username).first()
	last_date_submitted = ''
	if project.chapters is not None:
		last_date_submitted = project.chapters.order_by(Chapter.date_submitted.desc()).first().date_submitted
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.comment.data, user_id=current_user.id, project_id=project.id)
		db.session.add(comment)
		db.session.commit()
		return redirect(url_for('project_synopsis', id=project.id, title=project.title))
	genre = []
	for p in project.genre:
		genre.append(p.name)
	keywords = (', '.join(genre))
	comments = Comment.query.filter_by(project_id=project.id).order_by(Comment.timestamp.desc()).all()
	reviews = Rating.query.filter_by(project_id=project.id).order_by(Rating.timestamp.desc()).all()
	return render_template('project_synopsis.html', title=project.title, description=project.synopsis, keywords=keywords, project=project, form=form, comments=comments, reviews=reviews, last_date_submitted=last_date_submitted)
	
@app.route('/delete_project/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_project(id):
	project = Project.query.filter_by(id=id).first()
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
			if project.author is not current_user:
				return redirect(url_for('index'))'''
	db.session.delete(project)
	for p in project.chapters:
		session.delete(p)
	db.session.commit()
	return redirect(url_for('user', username=current_user.username))
	
@app.route('/delete_project/<id>', methods=['GET', 'POST'])
@login_required
def quarantine_project(id):
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
			return redirect(url_for('index'))'''
	project = Project.query.filter_by(id=id).first()
	project.date_quarantined = datetime.utcnow()
	db.session.commit()
	return redirect(url_for('index'))
	
@app.route('/unpublish_project/<id>', methods=['GET', 'POST'])
@login_required
def unpublish_project(id):
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
				return redirect(url_for('index'))'''
	project = Project.query.filter_by(id=id).first()
	project.date_published = None
	db.session.commit()
	return redirect(url_for('index'))
	
@app.route('/upvote/<int:id>', methods=['GET', 'POST'])
@login_required
def upvote(id):
	user = User.query.filter_by(username=current_user.username).first()
	project = Project.query.filter_by(id=id).first()
	project.upvotes(user)
	db.session.commit()
	return redirect(url_for('project_synopsis', id=project.id, title=project.title))
	
@app.route('/downvote/<int:id>', methods=['GET', 'POST'])
@login_required
def downvote(id):
	user = User.query.filter_by(username=current_user.username).first()
	project = Project.query.filter_by(id=id).first()
	project.downvotes(user)
	db.session.commit()
	return redirect(url_for('project_synopsis', id=project.id, title=project.title))
	
@app.route('/chapter/<id>', methods=['GET', 'POST'])
@login_required
def chapter(id):
	chapter = Chapter.query.filter_by(id=id).first()
	project = Project.query.filter_by(id=chapter.project_id).first()
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
			if project.author is not current_user:
				return redirect(url_for('index'))'''
	form = EditChapterForm()
	if form.save_chapter.data:
		print(form.edit_body.data)
		if form.validate_on_submit():
			print(form.edit_body.data)
			chapter.chapter_no = form.edit_chapter_number.data
			chapter.chapter_title = form.edit_chapter_title.data
			chapter.chapter_body = form.edit_body.data
			db.session.commit()
			return redirect(url_for('project', id=project.id, title=project.title))
	return render_template('chapter.html', chapter=chapter, project=project, form=form)
	
@app.route('/delete_chapter/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_chapter(id):
	chapter = Chapter.query.filter_by(id=id).first()
	project = Project.query.filter_by(id=chapter.project_id).first()
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
			if project.author is not current_user:
				return redirect(url_for('index'))'''
	db.session.delete(chapter)
	db.session.commit()
	return redirect(url_for('project', id=project.id, title=project.title))
	
@app.route('/add_to_library/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_library(id):
	user = User.query.filter_by(username=current_user.username).first()
	project = Project.query.filter_by(id=id).first()
	'''if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_authenticated:
		if current_user.is_superuser() == False:
			if project.author is not current_user:
				return redirect(url_for('index'))'''
	user.books.append(project)
	db.session.commit()
	return redirect(url_for('project', id=project.id, title=project.title))
	
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
	users = User.query.all()
	if current_user.is_anonymous:
		return redirect(url_for('index'))
	if current_user.is_superuser() == False:
		return redirect(url_for('index'))
	else:
		return render_template('admin.html', users=users)
	
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    '''Generate sitemap.xml iterating over static and dynamic routes to make a list of urls and date modified'''
    pages = []
    ten_days_ago = datetime.now() - timedelta(days=10)
    
    # get static routes
    for rule in current_app.url_map.iter_rules():
        # check for a 'GET' request and that the length of arguments is = 0 and if you have an admin area that the rule does not start with '/admin'
        if 'GET' in rule.methods and len(rule.arguments) == 0 and not rule.rule.startswith('/admin'):
            pages.append(['https://www.writerrific.com' + rule.rule, ten_days_ago.date().isoformat()])
            
    # get dynamic routes for blog
    projects = Project.query.filter(Project.date_published.isnot(None)).order_by(Project.date_published.desc()).all()
    for project in projects:
        url = 'https://www.writerrific.com' + url_for('project', id=project.id, title=project.title)
        modified_time = project.date_published.date().isoformat()
        pages.append([url, modified_time])
        
    sitemap_template = render_template('sitemap_template.xml', pages=pages)
    response = make_response(sitemap_template)
    response.headers["Content-Type"] = "application/xml"
    return response