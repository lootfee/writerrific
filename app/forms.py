from flask_wtf import FlaskForm
from app import app, photos
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, HiddenField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User
from flask_pagedown.fields import PageDownField

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	#username = StringField('Name', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')
	
class RegistrationForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(), Length(min=4, max=45)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(regex=r'^(?=\S{8,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])', message="Password must be atleasst 8 characters long, must contain an uppercase letter, a number and a special character.")])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
			
class EditProfileForm(FlaskForm):
	username = StringField('Pen Name', validators=[DataRequired(), Length(min=4, max=45)])
	about_me = TextAreaField('About me', validators=[Length(min=0, max=500)], render_kw={'maxlength': 500, "rows": 8, "cols": 10})
	email = StringField('Email', validators=[DataRequired(), Email()])
	profile_pic = FileField('Upload Profile Pic:', validators=[FileAllowed(photos)])
	submit = SubmitField('Submit')

	def __init__(self, original_username, original_email, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.original_username = original_username
		self.original_email = original_email

	def validate_username(self, username):
		if username.data != self.original_username:
			user = User.query.filter_by(username=self.username.data).first()
			if user is not None:
				raise ValidationError('Please use a different username.')
				
	def validate_email(self, email):
		if email.data != self.original_email:
			user = User.query.filter_by(email=self.email.data).first()
			if user is not None:
				raise ValidationError('Email is already registered!')
				
class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')
	
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Regexp(regex=r'^(?=\S{8,20}$)(?=.*?\d)(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[^A-Za-z\s0-9])', message="Password must be atleasst 8 characters long, must contain an uppercase letter, a number and a special character.")])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
	
class CreateProjectForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	genre = StringField('Topics', validators=[DataRequired()], render_kw={'placeholder': 'Separate each topic with a comma.'})
	synopsis = TextAreaField('Introduction', validators=[DataRequired(), Length(min=1, max=1000)], render_kw={'maxlength': 1000, 'placeholder': 'Maximum 1000 characters.'})
	cover_pic_link = StringField('Paste Cover Picture Link', render_kw={'placeholder': 'Paste your cover picture link or upload a pic below.'})
	cover_pic = FileField('Upload Cover Picture:', validators=[FileAllowed(photos)])
	cover_pic_credit = StringField('Picture credits ')
	submit = SubmitField('Submit')
	
class EditProjectForm(FlaskForm):
	proj_id = HiddenField('ID', validators=[DataRequired()])
	edit_title = StringField('Title', validators=[DataRequired()])
	edit_genre = StringField('Topics', validators=[DataRequired()])
	edit_synopsis = TextAreaField('Introduction', validators=[DataRequired(), Length(min=1, max=1000)], render_kw={'maxlength': 1000, 'placeholder': 'Maximum 1000 characters.'})
	#edit_synopsis = TextAreaField('Synopsis', validators=[DataRequired(), Length(min=1, max=1000)], render_kw={'maxlength': 1000, "rows": 5, "cols": 10})
	edit_cover_pic_link = StringField('Paste Cover Picture Link', render_kw={'placeholder': 'Paste your cover picture link or upload a pic below.'})
	edit_cover_pic = FileField('Upload Cover Picture:', validators=[FileAllowed(photos)], render_kw={'placeholder': 'Upload a cover picture or paste a link below.'})
	edit_cover_pic_credit = StringField('Picture credits ')
	edit_submit = SubmitField('Save')
	
class CreateChapterForm(FlaskForm):
	chapter_number = IntegerField('Chapter No:', validators=[DataRequired()])
	chapter_title = StringField('Chapter title:', validators=[DataRequired()])
	submit_chapter = SubmitField('Submit')
	
class EditChapterForm(FlaskForm):
	chapter_id = HiddenField('Chapter id:', validators=[DataRequired()])
	edit_chapter_number = IntegerField('Chapter No:', validators=[DataRequired()])
	edit_chapter_title = StringField('Chapter title:', validators=[DataRequired()])
	edit_body = PageDownField('Body', validators=[DataRequired()], render_kw={"rows": 20, "cols": 15})
	save = SubmitField('Save')

class PublishForm(FlaskForm):
	publish_project = SubmitField('Publish Project')
	
class CommentReviewForm(FlaskForm):
	post_for_advice = SubmitField('Post for advice')
	
class CommentForm(FlaskForm):
	comment = TextAreaField('Post a comment', validators=[DataRequired(), Length(min=1, max=1000)], render_kw={'maxlength': 1000})
	submit = SubmitField('Submit')
	
class ReviewForm(FlaskForm):
	review = TextAreaField('Write a review for ', validators=[DataRequired(), Length(min=1, max=1000)], render_kw={'maxlength': 1000, "rows": 6, "cols": 20})
	score = SelectField('Rating: (1 for Bad, 10 for Very Good)', choices=[('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5'), ('6','6'), ('7','7'), ('8','8'), ('9','9'), ('10','10')])
	submit_review = SubmitField('Submit')