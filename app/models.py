from datetime import datetime
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

	
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

votes = db.Table('votes',
	db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
)

upvotes = db.Table('upvotes',
	db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
)

downvotes = db.Table('downvotes',
	db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
)

library = db.Table('library',
	db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
)

genres = db.Table('genres',
	db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
	db.Column('genre_id', db.Integer, db.ForeignKey('genre.id')),
)

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	project = db.relationship('Project', backref='author', lazy='dynamic')
	chapter = db.relationship('Chapter', backref='author', lazy='dynamic')
	comment = db.relationship('Comment', backref='author', lazy='dynamic')
	review = db.relationship('Rating', backref='author', lazy='dynamic')
	about_me = db.Column(db.String(500))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)
		
	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self, user):
		return self.followed.filter(
			followers.c.followed_id == user.id).count() > 0
			
	def followed_posts(self):
		followed = Project.query.join(
			followers, (followers.c.followed_id == Project.user_id)).filter(
				followers.c.follower_id == self.id)
		own = Project.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Project.submission_date.desc())
		
	def get_reset_password_token(self, expires_in=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires_in},
			app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
			
				
	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)
		
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(1000))
	synopsis = db.Column(db.Text(50000))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	chapters = db.relationship('Chapter', backref='book', lazy='dynamic')
	#ratings = db.relationship('Rating', backref='book', lazy='dynamic')
	date_seek_review = db.Column(db.DateTime, index=True)
	date_published = db.Column(db.DateTime, index=True)
	
	comments = db.relationship('Comment', backref=db.backref('project', lazy=True), lazy='dynamic')
	ratings = db.relationship('Rating', backref=db.backref('project', lazy=True), lazy='dynamic')
	
	voters = db.relationship(
		'User', secondary='votes',
		backref=db.backref('votes', lazy='dynamic'), lazy='dynamic'
	)
	
	upvoters = db.relationship(
		'User', secondary='upvotes',
		backref=db.backref('upvotes', lazy='dynamic'), lazy='dynamic'
	)
	
	downvoters = db.relationship(
		'User', secondary='downvotes',
		backref=db.backref('downvotes', lazy='dynamic'), lazy='dynamic'
	)
	
	books = db.relationship(
		'User', secondary='library',
		backref=db.backref('books', lazy='dynamic'), lazy='dynamic'
	)
	
	genre = db.relationship(
		'Genre', secondary='genres',
		backref=db.backref('book', lazy='dynamic'), lazy='dynamic'
	)
	
	def is_purchased(self, user):
		return self.books.filter(
			library.c.user_id == user.id).count() > 0
		
	def voted(self, user):
		return self.voters.filter(votes.c.user_id == user.id).count() > 0
		
	def upvoted(self, user):
		return self.upvoters.filter(upvotes.c.user_id == user.id).count() > 0
		
	def downvoted(self, user):
		return self.downvoters.filter(downvotes.c.user_id == user.id).count() > 0
			
	def upvotes(self, user):
			if not self.voted(user):
				self.upvoters.append(user)
				self.voters.append(user)
			else:
				if self.upvoted(user):
					self.voters.remove(user)
					self.upvoters.remove(user)
				elif self.downvoted(user):
					self.downvoters.remove(user)
					self.upvoters.append(user)
				
				
	def downvotes(self, user):
			if not self.voted(user):
				self.downvoters.append(user)
				self.voters.append(user)
			else:
				if self.downvoted(user):
					self.voters.remove(user)
					self.downvoters.remove(user)
				elif self.upvoted(user):
					self.upvoters.remove(user)
					self.downvoters.append(user)
	
	
	def __repr__(self):
		return '<Project {} >'.format(self.title)
		
class Genre(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	
	def __repr__(self):
		return '<Genre {}>'.format(self.id)
		
class Chapter(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	chapter_no = db.Column(db.Integer)
	chapter_title = db.Column(db.String(1000))
	chapter_body = db.Column(db.Text(4294000000))
	project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	date_submitted = db.Column(db.DateTime, index=True, default=datetime.utcnow)
		
	def __repr__(self):
		return '<Chapter {}>'.format(self.id)
		

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(1000))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

	#reply = db.relationship('CommentReply', backref=db.backref('comment', lazy=True))
	
	def __repr__(self):
		return '<Comment {}>'.format(self.id)
		
class Rating(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	review = db.Column(db.String(1000))
	score = db.Column(db.Integer)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	
	def __repr__(self):
		return '<Rating {}>'.format(self.id)
