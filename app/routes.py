from flask import render_template, request, redirect, flash, url_for, abort, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from app.services.job_fetcher import fetch_job_listings
from app import app, db, bcrypt
from app.models import Meetings, Reviews, User, JobApplication, Recruiter_Postings, PostingApplications, JobExperience

from app.forms import RegistrationForm, LoginForm, ReviewForm, JobApplicationForm, PostingForm
from datetime import datetime
from app.util import extract_experience_summary, call_groq_api

app.config["SECRET_KEY"] = "5791628bb0b13ce0c676dfde280ba245"


@app.route("/")
@app.route("/home")
def home():
    """An API for the user to be able to access the homepage through the navbar"""
    entries = Reviews.query.all()
    return render_template("index.html", entries=entries)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password, is_recruiter=form.signup_as_recruiter.data
        )
        db.session.add(user)
        db.session.commit()
        flash(
            "Account created successfully! Please log in with your credentials.",
            "success",
        )
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash(
                "Login Unsuccessful. Please enter correct email and password.", "danger"
            )
    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))


@app.route("/review/all")
def view_reviews():
    """An API for the user to view all the reviews entered with pagination"""
    page = request.args.get("page", 1, type=int)
    per_page = 5
    entries = Reviews.query.paginate(page=page, per_page=per_page)
    return render_template("view_reviews.html", entries=entries)


@app.route("/review/new", methods=["GET", "POST"])
@login_required
def new_review():
    form = ReviewForm()
    if form.validate_on_submit():
        review = Reviews(
            job_title=form.job_title.data,
            job_description=form.job_description.data,
            department=form.department.data,
            locations=form.locations.data,
            hourly_pay=form.hourly_pay.data,
            benefits=form.benefits.data,
            review=form.review.data,
            rating=form.rating.data,
            recommendation=form.recommendation.data,
            author=current_user,
        )
        db.session.add(review)
        db.session.commit()
        flash("Review submitted successfully!", "success")
        return redirect(url_for("view_reviews"))
    return render_template(
        "create_review.html", title="New Review", form=form, legend="Add your Review"
    )


@app.route("/review/<int:review_id>")
def review(review_id):
    review = Reviews.query.get_or_404(review_id)
    return render_template("review.html", review=review)


@app.route("/review/<int:review_id>/update", methods=["GET", "POST"])
@login_required
def update_review(review_id):
    review = Reviews.query.get_or_404(review_id)
    if review.author != current_user:
        abort(403)
    form = ReviewForm()
    if form.validate_on_submit():
        review.job_title = form.job_title.data
        review.job_description = form.job_description.data
        review.department = form.department.data
        review.locations = form.locations.data
        review.hourly_pay = form.hourly_pay.data
        review.benefits = form.benefits.data
        review.review = form.review.data
        review.rating = form.rating.data
        review.recommendation = form.recommendation.data
        db.session.commit()
        flash("Your review has been updated!", "success")
        return redirect(url_for("view_reviews"))
    elif request.method == "GET":
        form.job_title.data = review.job_title
        form.job_description.data = review.job_description
        form.department.data = review.department
        form.locations.data = review.locations
        form.hourly_pay.data = review.hourly_pay
        form.benefits.data = review.benefits
        form.review.data = review.review
        form.rating.data = review.rating
        form.recommendation.data = review.recommendation
    return render_template(
        "create_review.html", title="Update Review", form=form, legend="Update Review"
    )


@app.route('/upvote/<int:review_id>', methods=['POST'])
@login_required
def upvote_review(review_id):
    review = Reviews.query.get_or_404(review_id)
    if review.upvotes is None:
        review.upvotes = 0  # Set to 0 if None
    review.upvotes += 1
    db.session.commit()
    flash('You upvoted the review!', 'success')
    return redirect(request.referrer or url_for('page_content_post'))


@app.route('/downvote/<int:review_id>', methods=['POST'])
@login_required
def downvote_review(review_id):
    review = Reviews.query.get_or_404(review_id)
    if review.upvotes is None:
        review.upvotes = 0  # Set to 0 if None
    if review.upvotes > 0:
        review.upvotes -= 1  # Decrement upvote count only if greater than 0
        db.session.commit()
        flash('You downvoted the review!', 'warning')
    return redirect(request.referrer or url_for('page_content_post'))


@app.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = Reviews.query.get_or_404(review_id)
    if review.author != current_user:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash("Your review has been deleted!", "success")
    return redirect(url_for("view_reviews"))


@app.route("/dashboard")
@login_required
def getVacantJobs():
    """
    An API for the users to see all the available vacancies and their details
    """
    postings = Recruiter_Postings.query.all()
    return render_template("dashboard.html", postings=postings)


@app.route("/apply/<int:posting_id>", methods=["POST"])
@login_required
def applyForJob(posting_id):
    postings = Recruiter_Postings.query.all()
    recruiter_id = request.form.get('recruiter_id')
    applicant_id = current_user.id
    existing_application = PostingApplications.query.filter_by(
        postingId=posting_id,
        recruiterId=recruiter_id,
        applicantId=applicant_id
    ).first()

    if existing_application:
        # If application exists, redirect or show a message
        flash("You have already applied for this job.", "warning")
        return render_template("dashboard.html", postings=postings)
    
    new_application = PostingApplications(
        postingId = posting_id,
        recruiterId = recruiter_id,
        applicantId = applicant_id
    )

    db.session.add(new_application)
    db.session.commit()

    flash("Application successfully submitted to the recruiter!", "success")
    return render_template("dashboard.html", postings=postings)


@app.route("/add_jobs", methods=['GET', 'POST'])
@login_required
def add_jobs():
    if not current_user.is_recruiter:
        flash("Unauthorized: You must be a recruiter to post jobs.", "danger")
        return redirect(url_for("home"))
    
    form = PostingForm()
    if form.validate_on_submit():
        posting = Recruiter_Postings(
            postingId = form.jobPostingID.data,
            recruiterId = current_user.id,
            jobTitle = form.jobTitle.data,
            jobLink = form.jobLink.data,
            jobDescription = form.jobDescription.data,
            jobLocation = form.jobLocation.data,
            jobPayRate = form.jobPayRate.data,
            maxHoursAllowed = form.maxHoursAllowed.data
        )
        print("Adding posting: ", posting)
        db.session.add(posting)
        db.session.commit()
        flash("Job Posting added successfully!", "success")
        return redirect(url_for("recruiter_postings"))
    return render_template(
        "add_jobs.html", title="Job Posting", form=form, legend="Add new posting"
    )

@app.route("/recruiter_postings")
@login_required
def recruiter_postings():
    if not current_user.is_recruiter:
        flash("Unauthorized: You must be a recruiter to post jobs.", "danger")
        return redirect(url_for("home"))
    
    postings = Recruiter_Postings.query.filter(Recruiter_Postings.recruiterId == current_user.id).all()
    return render_template(
        "recruiter_postings.html",
        postings=postings
    )

@app.route("/recruiter/postings/delete/<int:posting_id>", methods=["POST"])
def delete_posting(posting_id):
    if not current_user.is_recruiter:
        flash("Unauthorized: You must be a recruiter to post jobs.", "danger")
        return redirect(url_for("home"))
    
    # Fetch the posting by its ID
    posting = Recruiter_Postings.query.filter_by(postingId=posting_id, recruiterId=current_user.id).first()
    applicants_for_posting = PostingApplications.query.filter_by(postingId=posting_id, recruiterId=current_user.id).all()

    if applicants_for_posting:
        for application in applicants_for_posting:
            db.session.delete(application)
        db.session.commit()
    
    if posting:
        if posting.recruiterId == current_user.id:
            db.session.delete(posting)
            db.session.commit()
            flash("Job Posting deleted successfully!", "success")
        else:
            flash("You are not authorized to delete this posting", "danger")
    
    return redirect(url_for('recruiter_postings'))

@app.route("/recruiter/<int:posting_id>/applications", methods=["GET"])
@login_required
def get_applications(posting_id):
    """
    Display all applications for a specific job posting by the recruiter.
    """
    # Ensure the recruiter owns the posting
    posting = Recruiter_Postings.query.filter_by(
        postingId=posting_id, recruiterId=current_user.id
    ).first_or_404()

    # Fetch all applications for this posting
    applications = PostingApplications.query.filter_by(postingId=posting_id).all()

    # Create a list of user profiles associated with the applications
    application_user_profiles = []
    for application in applications:
        applicant = User.query.filter_by(id=application.applicantId).first()
        if applicant:
            application_user_profiles.append(applicant)

    # Pass the posting and the applicants to the template
    return render_template(
        "posting_applicants.html",
        posting=posting,
        application_user_profiles=application_user_profiles,
    )

@app.route("/recruiter/order-applicants/<int:posting_id>",methods=["GET"])
@login_required
def order_applicants(posting_id):
    """
    Order applicants from the incoming applicants for a specific job posting.
    """

    import json

    # Ensure the recruiter owns the posting
    posting = Recruiter_Postings.query.filter_by(
        postingId=posting_id, recruiterId=current_user.id
    ).first_or_404()

    # Fetch all applications for this posting
    applications = PostingApplications.query.filter_by(postingId=posting_id).all()

    # Create a list of user profiles associated with the applications
    application_user_profiles = []
    for application in applications:
        applicant = User.query.filter_by(id=application.applicantId).first()
        if applicant:
            experience_summary = extract_experience_summary(applicant)

            # Append the current applicant's experience summary in the list of summaries
            application_user_profiles.append(experience_summary)

    print(application_user_profiles)

    # Retrieve the posting details
    posting_data = posting.getJobDetails()
    
    # Form the input prompt
    input_prompt = "Job Description: " + posting_data['jobDescription'] + " \n " + json.dumps(application_user_profiles) + "\n Just give the output list."
    
    # Call GROQ AI API
    recommended_list = json.loads(call_groq_api("app\\prompts\\order_applicants_template.txt", input_prompt))

    # Reorder the JSONs as per the recommended list
    n = len(application_user_profiles)
    ordered_applications = [None] * n
    for i, p in enumerate(recommended_list):
        ordered_applications[i] = application_user_profiles[p - 1]

    # Add applicant id in each applicant data. applicant id is needed for "shortlisting candidate" functionality
    for application in ordered_applications:
        application['id'] = User.query.filter_by(username=application['username']).first().id

    # Pass the job description and the ordered applications to the template
    return render_template(
        "order_applicants_using_AI.html",
        posting=posting_data,
        applicants=ordered_applications
    )

@app.route("/applicant_profile/<string:applicant_username>", methods=["GET"])
@login_required
def get_applicant(applicant_username):
    job_experiences = JobExperience.query.filter_by(username=applicant_username).all()
    applicant_details = User.query.filter_by(username=applicant_username).first()

    print("Queried for: ", applicant_username)
    print(applicant_details.username)
    print("Job exp", job_experiences)

    return render_template(
        "applicant_profile.html",
        applicant_details=applicant_details,
        job_experiences=job_experiences
    )

@app.route("/pageContentPost", methods=["POST", "GET"])
def page_content_post():
    """An API for the user to view specific reviews depending on the job title, location, and rating range with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 5  # Set items per page as desired

    # Retrieve form data
    search_title = request.form.get("search_title", "")
    search_location = request.form.get("search_location", "")
    min_rating = request.form.get("min_rating", type=int, default=1)
    max_rating = request.form.get("max_rating", type=int, default=5)

    # Initial query for reviews
    query = Reviews.query

    # Apply filters if search fields are filled
    if search_title.strip():
        query = query.filter(Reviews.job_title.ilike(f"%{search_title}%"))
    if search_location.strip():
        query = query.filter(Reviews.locations.ilike(f"%{search_location}%"))
    if min_rating is not None and max_rating is not None:
        query = query.filter(Reviews.rating.between(min_rating, max_rating))

    # Paginate the results
    entries = query.paginate(page=page, per_page=per_page)

    # Pass search terms back to the template to preserve state across pagination
    return render_template(
        "view_reviews.html",
        entries=entries,
        search_title=search_title,
        search_location=search_location,
        min_rating=min_rating,
        max_rating=max_rating,
    )


@app.route("/account")
@login_required
def account():
    return render_template("account.html", title="Account")


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    job_listings = fetch_job_listings()
    return jsonify(job_listings)

@app.route("/job_application/new", methods=["GET", "POST"])
@login_required
def new_job_application():
    form = JobApplicationForm()  # Form class should include fields for job_link, applied_on, last_update_on, and status
    if form.validate_on_submit():
        # Create a new job application instance
        application = JobApplication(
            job_link=form.job_link.data,
            applied_on=form.applied_on.data,
            last_update_on=form.last_update_on.data,
            status=form.status.data,
            user_id=current_user.id  # Associate with the current logged-in user
        )
        db.session.add(application)
        db.session.commit()
        flash("Job application added successfully!", "success")
        return redirect(url_for("view_job_applications"))
    return render_template(
        "create_job_application.html",
        title="New Job Application",
        form=form,
        legend="Add Job Application"
    )

@app.route("/application_tracker")
@login_required
def application_tracker():
    # Query all job applications for the logged-in user
    job_applications = JobApplication.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "job_applications.html",
        title="Application Tracker",
        job_applications=job_applications,
    )

@app.route("/add_job_application", methods=["POST"])
@login_required
def add_job_application():
    job_link = request.form.get('job_link')
    applied_on = request.form.get('applied_on')
    last_update_on = request.form.get('last_update_on')
    status = request.form.get('status')

    new_application = JobApplication(
        job_link=job_link,
        applied_on=datetime.strptime(applied_on, '%Y-%m-%d').date(),
        last_update_on=datetime.strptime(last_update_on, '%Y-%m-%d').date(),
        status=status,
        user_id=current_user.id
    )

    db.session.add(new_application)
    db.session.commit()

    flash("Job application added successfully!", "success")
    return redirect(url_for('application_tracker'))

@app.route("/update_status/<int:application_id>", methods=["POST"])
@login_required
def update_status(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if application.user_id != current_user.id:
        flash("You cannot update this application.", "danger")
        return redirect(url_for('application_tracker'))

    status = request.form.get('status')
    application.status = status
    db.session.commit()

    flash("Application status updated successfully!", "success")
    return redirect(url_for('application_tracker'))

@app.route("/update_last_update/<int:application_id>", methods=["POST"])
@login_required
def update_last_update(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if application.user_id != current_user.id:
        flash("You cannot update this application.", "danger")
        return redirect(url_for('application_tracker'))

    last_update_on = request.form.get('last_update_on')
    application.last_update_on = datetime.strptime(last_update_on, '%Y-%m-%d').date()
    db.session.commit()

    flash("Application last update date updated successfully!", "success")
    return redirect(url_for('application_tracker'))

@app.route("/delete_job_application/<int:application_id>", methods=["POST"])
@login_required
def delete_job_application(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if application.user_id != current_user.id:
        flash("You cannot delete this application.", "danger")
        return redirect(url_for('application_tracker'))

    db.session.delete(application)
    db.session.commit()
    flash("Job application deleted successfully!", "success")
    return redirect(url_for('application_tracker'))

@app.route('/job_profile', methods=['GET', 'POST'])
@login_required
def job_profile():
    if request.method == 'POST':
        # Handle job experience form submission
        job_title = request.form.get('job_title')
        company_name = request.form.get('company_name')
        location = request.form.get('location')
        duration = request.form.get('duration')
        description = request.form.get('description')
        skills = request.form.get('skills') 

        new_job = JobExperience(
            job_title=job_title,
            company_name=company_name,
            location=location,
            duration=duration,
            description=description,
            skills=skills,
            username=current_user.username
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job experience added successfully!', 'success')
        return redirect(url_for('job_profile'))

    # Fetch job experiences for the current user
    job_experiences = JobExperience.query.filter_by(username=current_user.username).all()
    return render_template('job_profile.html', job_experiences=job_experiences)

@app.route('/schedule_meeting/<string:applicant_username>', methods=['POST'])
@login_required
def schedule_meeting(applicant_username):
    meeting_time_str = request.form.get('meeting_time')  # Get the meeting time
    posting_id = request.form.get('posting_id')  # Get the posting ID

    try:
        # Convert the meeting time string to a datetime object
        meeting_time = datetime.strptime(meeting_time_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Invalid date format. Please use the provided date-time picker.", "danger")
        return redirect(request.referrer)

    # Validate posting ID
    if not posting_id:
        flash("No job posting associated with this meeting.", "danger")
        return redirect(request.referrer)

    # Fetch the applicant from the database
    applicant = User.query.filter_by(username=applicant_username).first()
    if not applicant:
        flash("Applicant not found.", "danger")
        return redirect(request.referrer)

    # Validate the job posting exists
    job_posting = Recruiter_Postings.query.filter_by(postingId=posting_id, recruiterId=current_user.id).first()
    if not job_posting:
        flash("Job posting not found or you are not authorized to schedule a meeting for this posting.", "danger")
        return redirect(request.referrer)

    # Create and save the meeting
    new_meeting = Meetings(
        recruiter_id=current_user.id,
        applicant_id=applicant.id,
        meeting_time=meeting_time,
        posting_id=posting_id  # Associate the meeting with the job posting
    )

    db.session.add(new_meeting)
    db.session.commit()

    flash(f"Meeting scheduled with {applicant_username} on {meeting_time} for job posting '{job_posting.jobTitle}'.", "success")
    return redirect(request.referrer)

@app.route('/recruiter/meetings', methods=['GET'])
@login_required
def recruiter_meetings():
    meetings = Meetings.query.filter_by(recruiter_id=current_user.id).all()
    return render_template("recruiter_meetings.html", meetings=meetings)

@app.route('/applicant/meetings', methods=['GET'])
@login_required
def applicant_meetings():
    meetings = Meetings.query.filter_by(applicant_id=current_user.id).all()
    return render_template("applicant_meetings.html", meetings=meetings)
@app.route('/shortlisted/<int:posting_id>', methods=['GET'])
@login_required
def view_shortlisted_for_posting(posting_id):
    """
    Fetch and display all shortlisted applicants for a specific job posting.
    """
    # Ensure the current user is the recruiter for this posting
    posting = Recruiter_Postings.query.filter_by(postingId=posting_id, recruiterId=current_user.id).first_or_404()

    # Fetch all shortlisted applicants for the job posting
    shortlisted_applicants = PostingApplications.query.filter_by(
        postingId=posting_id,
        recruiterId=current_user.id,
        shortlisted=True
    ).all()

    return render_template("shortlisted_applicants.html", posting=posting, applicants=shortlisted_applicants)


@app.route('/shortlisted', methods=['GET'])
@login_required
def view_all_shortlisted():
    """
    Fetch and display all shortlisted applicants for all job postings of the recruiter.
    """
    if not current_user.is_recruiter:
        flash("Unauthorized access! Only recruiters can view this page.", "danger")
        return redirect(url_for('home'))

    # Fetch all job postings for the current recruiter
    job_postings = Recruiter_Postings.query.filter_by(recruiterId=current_user.id).all()

    # Create a dictionary to group shortlisted applicants by job postings
    shortlisted_by_posting = {}
    for posting in job_postings:
        shortlisted_by_posting[posting] = PostingApplications.query.filter_by(
            postingId=posting.postingId,
            recruiterId=current_user.id,
            shortlisted=True
        ).all()

    return render_template(
        "shortlisted_applicants.html",
        shortlisted_by_posting=shortlisted_by_posting
    )


@app.route('/shortlist/<int:posting_id>/<int:applicant_id>', methods=['POST'])
@login_required
def toggle_shortlist(posting_id, applicant_id):
    """
    Toggle the shortlisted status of an applicant for a specific job posting.
    """
    application = PostingApplications.query.filter_by(
        postingId=posting_id,
        recruiterId=current_user.id,
        applicantId=applicant_id
    ).first_or_404()

    # Toggle shortlist status
    application.shortlisted = not application.shortlisted
    db.session.commit()

    # Add a flash message for feedback
    flash(
        f"Applicant {'shortlisted' if application.shortlisted else 'unshortlisted'} successfully!",
        "success"
    )

    # Redirect back to the referring page
    return redirect(request.referrer)

@app.route('/search_candidates', methods=['GET', 'POST'])
@login_required
def search_candidates():
    if not current_user.is_recruiter:
        flash("Unauthorized access! Only recruiters can access this page.", "danger")
        return redirect(url_for('home'))

    job_experiences = []
    if request.method == 'POST':
        # Get search type (role or skills) and search query
        search_type = request.form.get('search_type')
        search_query = request.form.get('search_query', '').strip()

        # Base query: Fetch job experiences with related user information
        query = db.session.query(JobExperience, User).join(User).filter(User.is_recruiter == False)

        # Apply filters based on the search type
        if search_query:
            if search_type == 'role':
                query = query.filter(JobExperience.job_title.ilike(f"%{search_query}%"))
            elif search_type == 'skills':
                query = query.filter(JobExperience.skills.ilike(f"%{search_query}%"))

        # Execute query
        job_experiences = query.all()

    return render_template('search_candidates.html', job_experiences=job_experiences)

