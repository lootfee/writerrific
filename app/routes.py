from flask import render_template, flash, redirect, url_for, request, current_app, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, CreateProjectForm, EditProjectForm, CreateChapterForm, EditChapterForm, CommentForm, PublishForm, ReviewForm, CommentReviewForm
from app.models import User, Project, Comment, Chapter, Genre, Rating
from datetime import datetime, timedelta
import markdown2 



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
		

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
	return render_template('home.html', title='Home')


@app.route('/explore', methods=['GET', 'POST'])
def index():
	page = request.args.get('page', 1, type=int)
	projects = Project.query.order_by(Project.date_published.desc()).filter(Project.date_published.isnot(None)).filter_by(date_quarantined=None).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=projects.next_num) \
		if projects.has_next else None
	prev_url = url_for('index', page=projects.prev_num) \
		if projects.has_prev else None
	return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url)
	
@app.route('/advice', methods=['GET', 'POST'])
def advice():
	page = request.args.get('page', 1, type=int)
	for_advice_projects = Project.query.order_by(Project.date_published.desc()).filter(Project.date_seek_review.isnot(None)).filter_by(date_published=None, date_quarantined=None).paginate(
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
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))	
	
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thank you for registering')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
	
@app.route('/user/<username>', methods=['GET', 'POST'])
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	portfolio = Project.query.filter_by(user_id=user.id, date_quarantined=None).all()
	for p in portfolio:
		pg_list = []
		for pg in p.genre:
			pg_list.append(pg.name)
		p.pg_name = ','.join(pg_list)
	library = user.books.filter_by(date_quarantined=None).all()
	form = CreateProjectForm()
	form2 = EditProjectForm()
	if form.submit.data:
		if form.validate_on_submit():
			genres = form.genre.data
			genre_list = genres.split(',')
			proj = Project(title=form.title.data, synopsis=form.synopsis.data, user_id=current_user.id)
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
			return redirect(url_for('user', username=current_user.username))
	elif form2.edit_submit.data:
		if form2.validate_on_submit():
			edit_proj = Project.query.filter_by(id=form2.proj_id.data).first()
			edit_proj.title = form2.edit_title.data
			#edit_proj.edit_genre = form2.edit_genre.data
			edit_proj.synopsis = form2.edit_synopsis.data
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
			#return redirect(url_for('user', username=current_user.username))
			db.session.commit()
			return redirect(url_for('user', username=current_user.username))
	'''elif request.method == 'GET':
		for p in portfolio:
			form2.proj_id.data = p.id
			form2.edit_title.data = p.title
			form2.edit_genre.data = p.genre
			form2.edit_synopsis.data = p.synopsis'''
	return render_template('user.html', user=user, title='User', form=form, form2=form2, portfolio=portfolio, library=library)
	
	
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username, current_user.email)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		current_user.email = form.email.data
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
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for instructions on how to reset your password.')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html', title='Reset Password', form=form)
	
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
	
@app.route('/project/<id>/<title>', methods=['GET', 'POST'])
def project(id, title):
	project = Project.query.filter_by(id=id).first()
	chapters = Chapter.query.filter_by(project_id=project.id).order_by(Chapter.chapter_no.asc()).all()
	form = CreateChapterForm()
	if form.submit_chapter.data and form.validate_on_submit():
		chapter = Chapter(chapter_no=form.chapter_number.data, chapter_title=form.chapter_title.data, project_id=project.id, author_id=current_user.id)
		db.session.add(chapter)
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	for c in chapters:
		if c.chapter_body is not None:
			c.body = markdown2.markdown(c.chapter_body)
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
	return render_template('project.html', project=project, form=form, form1=form1, form2=form2, form3=form3, chapters=chapters)
	
@app.route('/project_synopsis/<id>/<title>', methods=['GET', 'POST'])
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
	comments = Comment.query.filter_by(project_id=project.id).order_by(Comment.timestamp.desc()).all()
	reviews = Rating.query.filter_by(project_id=project.id).order_by(Rating.timestamp.desc()).all()
	return render_template('project_synopsis.html', project=project, form=form, comments=comments, reviews=reviews, last_date_submitted=last_date_submitted)
	
@app.route('/quarantine_project/<id>', methods=['GET', 'POST'])
@login_required
def quarantine_project(id):
	project = Project.query.filter_by(id=id).first()
	project.date_quarantined = datetime.utcnow()
	db.session.commit()
	return redirect(url_for('index'))
	
@app.route('/unpublish_project/<id>', methods=['GET', 'POST'])
@login_required
def unpublish_project(id):
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
	form = EditChapterForm()
	if form.validate_on_submit():
		chapter.chapter_no = form.edit_chapter_number.data
		chapter.chapter_title = form.edit_chapter_title.data
		chapter.chapter_body = form.edit_body.data
		db.session.commit()
		return redirect(url_for('project', id=project.id, title=project.title))
	return render_template('chapter.html', chapter=chapter, project=project, form=form)
	
@app.route('/add_to_library/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_library(id):
	user = User.query.filter_by(username=current_user.username).first()
	project = Project.query.filter_by(id=id).first()
	user.books.append(project)
	db.session.commit()
	return redirect(url_for('project', id=project.id, title=project.title))
	
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