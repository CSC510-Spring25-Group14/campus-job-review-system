"""Module for handling form definitions using Flask-WTF."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    RadioField,
    TextAreaField,
    DateField,
    SelectField,
    IntegerField
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL
from app.models import User


class RegistrationForm(FlaskForm):
    """Form for user registration."""

    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    signup_as_recruiter = BooleanField('Signup as Recruiter')
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        """Validate that the username is unique."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "The username is taken. Please choose a different username."
            )

    def validate_email(self, email):
        """Validate that the email is unique."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("An account already exists with this email address.")


class LoginForm(FlaskForm):
    """Form for user login."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ReviewForm(FlaskForm):
    """Form for submitting a job review."""

    department = StringField("Department", validators=[DataRequired()])
    locations = StringField("Location", validators=[DataRequired()])
    job_title = StringField("Job Title", validators=[DataRequired()])
    job_description = StringField("Job Description", validators=[DataRequired()])
    hourly_pay = StringField("Hourly Pay", validators=[DataRequired()])
    benefits = StringField("Benefits", validators=[DataRequired()])
    review = TextAreaField("Review", validators=[DataRequired()])
    rating = RadioField(
        "Rating",
        validators=[DataRequired()],
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
    )
    recommendation = RadioField(
        "Recommendation",
        validators=[DataRequired()],
        choices=[
            (1, "1"),
            (2, "2"),
            (3, "3"),
            (4, "4"),
            (5, "5"),
            (6, "6"),
            (7, "7"),
            (8, "8"),
            (9, "9"),
            (10, "10"),
        ],
    )
    submit = SubmitField("Submit your review")


class JobApplicationForm(FlaskForm):
    job_link = StringField("Job Link", validators=[DataRequired(), URL()])
    applied_on = DateField("Applied On", validators=[DataRequired()])
    last_update_on = DateField("Last Update On", validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[("applied", "Applied"), ("phone_screen", "Phone Screen"), 
                 ("technical", "Technical"), ("offer", "Offer")],
        validators=[DataRequired()]
    )
    submit = SubmitField("Save")

class PostingForm(FlaskForm):
    """Form for submitting a job posting."""

    jobPostingID = IntegerField("Posting ID", validators=[DataRequired()])
    jobTitle = StringField("Job Title", validators=[DataRequired()])
    jobLink = StringField("Job Link", validators=[DataRequired()])
    jobDescription = TextAreaField("Job Description", validators=[DataRequired()])
    jobLocation = StringField("Job Location", validators=[DataRequired()])
    jobPayRate = StringField("Job Pay Rate", validators=[DataRequired()])
    maxHoursAllowed = IntegerField("Max Hours Allowed", validators=[DataRequired()])
    submit = SubmitField("Submit Posting")
