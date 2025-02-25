import os
import sys
import pytest
import json
from app import app, db
from app.models import Meetings, User, Reviews, JobApplication, JobExperience, Recruiter_Postings, PostingApplications
from datetime import datetime
from unittest.mock import patch
from flask import url_for 
from flask_login import login_user, current_user
from app.util import call_groq_api

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def create_reviews(client, login_user):
    """Fixture to create multiple reviews for testing."""
    # Create a user for reviews
    user = User(username="testuser1", email="test1@example.com", password="testpassword2")
    db.session.add(user)
    db.session.commit()

    # Create sample reviews
    for i in range(10):
        review = Reviews(
            job_title=f"Software Engineer {i}",
            job_description="Description for Software Engineer.",
            department="Engineering",
            locations="New York",
            hourly_pay="30",
            benefits="Health insurance",
            review="This is a sample review.",
            rating=4,
            recommendation="Yes",
            author=user  # Set the author to the created user
        )
        db.session.add(review)

    db.session.commit()  # Commit all the reviews to the database

    yield  # This allows the test to run after setting up

    # Optionally clear the reviews after tests
    Reviews.query.delete()
    db.session.commit()


@pytest.fixture
def login_user(client):
    user = User(username="testuser", email="testuser@example.com", password="testpassword", is_recruiter=True)
    db.session.add(user)
    db.session.commit()

    # Log in the user
    with client.session_transaction() as session:
        session['user_id'] = user.id
        
    return user

@pytest.fixture
def create_review(login_user):
    review = Reviews(job_title="Test Job", job_description="Test Description",
                     department="Test Department", locations="Test Location",
                     hourly_pay="20", benefits="None", review="Great job!",
                     rating=5, recommendation="Yes", author=login_user)
    db.session.add(review)
    db.session.commit()
    return review

@pytest.fixture
def test_review():
    review = Reviews(
        department="Engineering",
        locations="Remote",
        job_title="Test Job",
        job_description="This is a test job description.",
        hourly_pay="50",
        benefits="Health Insurance, Paid Time Off",
        review="Great place to work!",
        rating=5,
        recommendation=1,  # Assuming 1 means "Yes" and 0 means "No"
        upvotes=0,  # Initial upvote count
        user_id=1  # Ensure this matches a valid user in your test database
    )
    db.session.add(review)
    db.session.commit()
    return review

@pytest.fixture
def test_job_applications(login_user):
    # Add multiple job applications for the test user
    applications = [
        JobApplication(
            job_link="https://company-a.com/jobs/software-engineer",
            applied_on=datetime(2024, 1, 15).date(),
            last_update_on=datetime(2024, 1, 20).date(),
            status="Applied",
            user_id=login_user.id,
        ),
        JobApplication(
            job_link="https://company-b.com/jobs/data-scientist",
            applied_on=datetime(2024, 2, 10).date(),
            last_update_on=datetime(2024, 2, 15).date(),
            status="Interview Scheduled",
            user_id=login_user.id,
        ),
    ]
    db.session.add_all(applications)
    db.session.commit()
    return applications

@pytest.fixture
def test_job_experiences(login_user):
    experiences = [
        JobExperience(
            job_title="Software Engineer",
            company_name="TechCorp",
            location="Remote",
            duration="2 years",
            description="Worked on web applications.",
            username=login_user.username
        ),
        JobExperience(
            job_title="Data Scientist",
            company_name="DataCorp",
            location="New York",
            duration="1 year",
            description="Analyzed large datasets.",
            username=login_user.username
        )
    ]
    db.session.add_all(experiences)
    db.session.commit()
    return experiences


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_index_route_2(client):
    response = client.get('/home')
    assert response.status_code == 200

def test_register_get(client):
    response = client.get('/register')
    assert response.status_code == 200

def test_register_post(client):
    response = client.post('/register', data={
        'username': 'asavla2',
        'password': 'pass',
        'email': 'asavla2@ncsu.edu'
    })
    assert response.status_code == 200

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_login_post(client):
    response = client.post('/login', data={
        'email': 'asavla2@ncsu.edu',
        'password': 'pass'
    })
    assert response.status_code == 200

def test_logout_get(client):
    response = client.get('/logout')
    assert response.status_code == 302

def test_view_review_all(client):
    response = client.get('/review/all')
    assert response.status_code == 200

def test_add_review_route_get(client):
    response = client.get('/review/new')
    assert response.status_code == 302

def test_add_review_route_post(client):
    response = client.post('/review/new', data={
        "job_title": "1",
        "job_description": "2",
        "department": "3",
        "locations": "4",
        "hourly_pay": "5",
        "benefits": "6",
        "review": "7",
        "rating": "2",
        "recommendation": "2",
    })
    assert response.status_code == 302

def test_view_review(client, create_review):
    response1 = client.get(f'/review/{create_review.id}')
    assert response1.status_code == 200

    response2 = client.get('/review/9999')  # Non-existent review ID
    assert response2.status_code == 404  # Should return 404 for non-existent review

def test_update_review_get(client, login_user, create_review):
    # Check that a logged-in user can access the update page
    response = client.get(f'/review/{create_review.id}/update', follow_redirects=True)
    assert response.status_code == 200  # Should be accessible to the author

def test_update_review_post(client, login_user, create_review):
    # Test updating a review
    response = client.post(f'/review/{create_review.id}/update', data={
        "job_title": "Updated Job",
        "job_description": "Updated Description",
        "department": "Updated Department",
        "locations": "Updated Location",
        "hourly_pay": "30",
        "benefits": "More Benefits",
        "review": "Updated review text.",
        "rating": "4",
        "recommendation": "No",
    }, follow_redirects=True)
    assert response.status_code == 200  # Check if it updates successfully

def test_dashboard_route(client):
    response = client.get('/dashboard', follow_redirects = True)
    assert response.status_code == 200

def test_account_route(client):
    response = client.get('/account')
    assert response.status_code == 302

def test_get_jobs(client):
    response = client.get('/api/jobs')
    assert response.status_code == 200

def test_new_review(client, login_user):
    # Log in the user
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  # Simulate user login

    # Prepare the data to submit a new review
    review_data = {
        "job_title": "Software Engineer",
        "job_description": "Develops software applications.",
        "department": "Engineering",
        "locations": "Remote",
        "hourly_pay": "50",
        "benefits": "Health Insurance, Paid Time Off",
        "review": "Great place to work!",
        "rating": "5",
        "recommendation": "Yes",
    }

    # Submit the new review
    response = client.post('/review/new', data=review_data, follow_redirects=True)

    # Check if the response is a redirect to the view reviews page
    assert response.status_code == 200  # Ensure the response is OK after redirect

def test_delete_review(client, login_user, create_review):
    # Log in the user
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  # Simulate user login

    # Submit the delete request
    response = client.post(f'/review/{create_review.id}/delete', follow_redirects=True)

    # Check if the response is a redirect to the view reviews page
    assert response.status_code == 200

def test_page_content_post(client, create_reviews):  # Assuming create_reviews is a fixture that populates the database
    # Prepare the search parameters
    response = client.post('/pageContentPost', data={
        'search_title': 'Software Engineer',
        'search_location': 'New York',
        'min_rating': 3,
        'max_rating': 5
    }, follow_redirects=True)

    # Check if the response is successful
    assert response.status_code == 200

    # Check if the response contains the relevant reviews
    assert b'Software Engineer' in response.data
    assert b'New York' in response.data

    # Verify that the rating is within the specified range
    for review in Reviews.query.all():  # Assuming Reviews is a model that can be queried
        if review.rating:
            assert 3 <= review.rating <= 5  # Check if the review rating is within the specified range


def test_page_content_post_pagination(client, create_reviews):  # Assuming create_reviews creates more than 5 reviews
    # Request the first page
    response = client.post('/pageContentPost?page=1', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Pagination' in response.data  # Check for pagination element

    # Request the second page
    response = client.post('/pageContentPost?page=2', data={}, follow_redirects=True)
    assert response.status_code == 200


def test_page_content_post_search_criteria_persistence(client, create_reviews):
    # Perform a search with specific parameters
    response = client.post('/pageContentPost', data={
        'search_title': 'Software Engineer',
        'search_location': 'New York',
        'min_rating': 3,
        'max_rating': 5
    }, follow_redirects=True)

    # Check if the response is successful
    assert response.status_code == 200

    # Verify that the search criteria are retained in the response
    assert b'Software Engineer' in response.data
    assert b'New York' in response.data
    assert b'3' in response.data  # Check if the min rating is displayed
    assert b'5' in response.data  # Check if the max rating is displayed

# Test home page access
def test_home_page_access(client):
    response = client.get('/', follow_redirects=True)
    assert b'nc state campus jobs' in response.data.lower()


# Test unauthorized access to account page
def test_account_route_requires_login(client):
    response = client.get('/account', follow_redirects=True)
    assert b'login' in response.data.lower()


# Test user registration with invalid email
def test_register_invalid_email(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'invalid-email',
        'password': 'pass',
        'confirm_password': 'pass'
    }, follow_redirects=True)
    assert b'invalid' in response.data.lower()


# Test pagination limit on reviews
def test_review_pagination_limit(client, create_review):
    response = client.get('/review/all?page=1', follow_redirects=True)
    assert b'page' in response.data.lower()  # Confirm pagination element


# Test static file access
def test_static_files_served(client):
    response = client.get('/static/css/style.css')
    assert response.data.strip() != b''


# Test CSRF protection with a fake CSRF token
def test_csrf_protection_on_review_form(client):
    response = client.post('/review/new', data={
        "job_title": "Test",
        "job_description": "Test",
        "locations": "Test",
        "hourly_pay": "20",
        "benefits": "None",
        "review": "Nice job!",
        "rating": "5",
        "recommendation": "Yes",
    }, follow_redirects=True)
    assert b'alert' in response.data.lower()


# Test unauthorized review update attempt
def test_update_review_permission_denied(client, create_review):
    another_user = User(username="otheruser", email="other@example.com", password="password")
    db.session.add(another_user)
    db.session.commit()

    with client.session_transaction() as session:
        session['user_id'] = another_user.id

    response = client.post(f'/review/{create_review.id}/update', data={
        "job_title": "Unauthorized Update",
    }, follow_redirects=True)
    assert b'alert' in response.data.lower()


# Test login with remember me option
def test_login_remember_me(client):
    user = User(username="rememberme", email="remember@example.com", password="password")
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'email': 'remember@example.com',
        'password': 'password',
        'remember': True
    }, follow_redirects=True)
    assert b'ncsu campus job' in response.data.lower()


# Test dashboard job listings display
def test_dashboard_jobs_display(client):
    with patch('app.services.job_fetcher.fetch_job_listings') as mock_fetch:
        mock_fetch.return_value = [
            {"title": "Job 1", "link": "http://example.com/job1"},
            {"title": "Job 2", "link": "http://example.com/job2"},
        ]
        response = client.get('/dashboard', follow_redirects=True)
        assert b'job' in response.data.lower()


def test_register_password_mismatch(client):
    response = client.post('/register', data={
        'username': 'mismatchuser',
        'email': 'mismatch@example.com',
        'password': 'password123',
        'confirm_password': 'differentpassword'
    }, follow_redirects=True)
    assert b'field must be equal to password' in response.data.lower()


# Test accessing account page without logging in
def test_invalid_account_access(client):
    response = client.get('/account', follow_redirects=True)
    assert b'login' in response.data.lower()


# Test user session persistence after login
def test_user_session_persistence(client, login_user):
    with client.session_transaction() as session:
        assert session.get('user_id') == login_user.id


# Test for add jobs GET request
def test_add_jobs_get_request(client, login_user):
    # Log in as a recruiter
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.get('/add_jobs')

    assert response.status_code == 200


# Test for add jobs POST request to upload new job postings
def test_add_jobs_post_request(client, login_user):
    # Log in as a recruiter
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True

    form_data = {
        'jobPostingID': '12345',
        'jobTitle': 'Software Engineer',
        'jobLink': 'https://example.com/job',
        'jobDescription': 'Develop and maintain software applications.',
        'jobLocation': 'Remote',
        'jobPayRate': '50',
        'maxHoursAllowed': '40'
    }

    response = client.post('/add_jobs', data=form_data, follow_redirects=True)

    assert response.status_code == 200
    

# Test recruiters posting fetch query
def test_recruiter_postings_as_recruiter(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True

    # Create some sample postings for the recruiter
    from app.models import Recruiter_Postings
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop and maintain software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )

    db.session.add(posting)
    db.session.commit()

    # Send GET request
    response = client.get('/recruiter_postings')

    # Assert response status
    assert response.status_code == 200


# Test delete posting for recruiter
def test_delete_posting_as_recruiter(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True

    # Create a posting to delete
    from app.models import Recruiter_Postings, db
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop and maintain software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    # Send POST request to delete the posting
    response = client.post(f'/recruiter/postings/delete/{posting.postingId}', follow_redirects=True)

    # Assert redirection to recruiter_postings page
    assert response.status_code == 200


# Test application for the job
def test_apply_for_job_first_time(client, login_user):
    
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.post(f'/apply/{posting.postingId}', data={
        'recruiter_id': login_user.id
    }, follow_redirects=True)

    assert response.status_code == 200


# Test applying for the already applied job
def test_apply_for_job_already_applied(client, login_user):    
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    # Apply for the job for the first time
    client.post(f'/apply/{posting.postingId}', data={'recruiter_id': login_user.id}, follow_redirects=True)

    # Try applying again for the same job
    response = client.post(f'/apply/{posting.postingId}', data={'recruiter_id': login_user.id}, follow_redirects=True)

    assert response.status_code == 200

# Test get applications request for recruiters
def test_get_applications(client, login_user):    
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    # Create an application for this job by the applicant
    application = PostingApplications(
        postingId=posting.postingId,
        recruiterId=login_user.id,
        applicantId=login_user.id
    )
    db.session.add(application)
    db.session.commit()

    response = client.get(f'/recruiter/{posting.postingId}/applications')

    assert response.status_code == 302


# Test get applications request without applicants for recruiters
def test_get_applications_no_applications(client, login_user):
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.get(f'/recruiter/{posting.postingId}/applications')

    assert response.status_code == 302


# Test get applicants for a recruiter posting
def test_get_applicant_profile(client, login_user):    
    job_experience = JobExperience(
        username=login_user.username,
        company_name="Example Corp",
        job_title="Software Developer",
        location="Raleigh",
        duration="1 year",
        description="Software Engineering"
    )
    db.session.add(job_experience)
    db.session.commit()

    response = client.get(f'/applicant_profile/{login_user.username}')

    assert response.status_code == 302


# Test review creation with invalid rating input
def test_create_review_invalid_rating(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.post('/review/new', data={
        "job_title": "Test Job",
        "job_description": "Description",
        "department": "Department",
        "locations": "Location",
        "hourly_pay": "20",
        "benefits": "Health",
        "review": "Good",
        "recommendation": "Yes",
    }, follow_redirects=True)
    print(response.data.lower().decode('utf-8'))
    assert b'alert' in response.data.lower() or b'invalid' in response.data.lower()


# Test viewing a non-existent review
def test_view_nonexistent_review(client):
    response = client.get('/review/9999', follow_redirects=True)
    assert b'not found' in response.data.lower()

def test_upvote_review(client, login_user, test_review):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  

    response = client.post(f'/upvote/{test_review.id}', follow_redirects=True)

    assert response.status_code == 200

def test_downvote_review(client, login_user, test_review):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  

    response = client.post(f'/downvote/{test_review.id}', follow_redirects=True)

    assert response.status_code == 200

def test_application_tracker_authenticated(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  

    response = client.get("/application_tracker", follow_redirects=True)

    assert response.status_code == 200

def test_application_tracker_authenticated(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id  

    response = client.post("/add_job_application", follow_redirects=True)

    assert response.status_code == 200

def test_update_status_success(client, login_user, test_job_applications):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    application_id = test_job_applications[0].id
    response = client.post(f"/update_status/{application_id}", data={"status": "Interview Scheduled"}, follow_redirects=True)

    assert response.status_code == 200

def test_delete_job_application_success(client, login_user, test_job_applications):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    application_id = test_job_applications[0].id
    response = client.post(f"/delete_job_application/{application_id}", follow_redirects=True)

    assert response.status_code == 200
    
def test_update_last_update_success(client, login_user, test_job_applications):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    application_id = test_job_applications[0].id
    response = client.post(
        f"/update_last_update/{application_id}",
        data={"last_update_on": "2024-11-01"},
        follow_redirects=True
    )

    assert response.status_code == 200

def test_job_profile_get(client, login_user, test_job_experiences):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.get('/job_profile', follow_redirects = True)

    assert response.status_code == 200
    print("responsee:",response.data)
    experience = JobExperience.query.filter_by(
        job_title="Software Engineer",
        company_name="TechCorp",
        username=login_user.username
    ).first()

    assert experience is not None
    assert experience.location == "Remote"
    assert experience.duration == "2 years"
    assert experience.description == "Worked on web applications."

def test_schedule_meeting_valid(client, login_user, test_job_experiences):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.post(
        f'/schedule_meeting/{login_user.username}',
        data={
            'meeting_time': '2024-12-01T10:00',
            'posting_id': test_job_experiences[0].id
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_schedule_meeting_invalid_date_format(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.post(
        f'/schedule_meeting/{login_user.username}',
        data={
            'meeting_time': 'invalid-date',
            'posting_id': 1
        },
        follow_redirects=True
    )
    assert response.status_code == 200  # Redirected due to flash message


def test_schedule_meeting_no_posting_id(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.post(
        f'/schedule_meeting/{login_user.username}',
        data={
            'meeting_time': '2024-12-01T10:00'
        },
        follow_redirects=True
    )
    assert response.status_code == 200  # Redirected due to flash message


def test_schedule_meeting_invalid_applicant(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.post(
        '/schedule_meeting/invalid_user',
        data={
            'meeting_time': '2024-12-01T10:00',
            'posting_id': 1
        },
        follow_redirects=True
    )
    assert response.status_code == 200  # Redirected due to flash message


def test_recruiter_meetings(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True  # Ensure recruiter access

    response = client.get('/recruiter/meetings', follow_redirects=True)
    assert response.status_code == 200


def test_applicant_meetings(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    response = client.get('/applicant/meetings', follow_redirects=True)
    assert response.status_code == 200


def test_view_shortlisted_for_posting_valid(client, login_user, test_job_experiences):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.get(f'/shortlisted/{test_job_experiences[0].id}', follow_redirects=True)
    assert response.status_code == 200


def test_view_all_shortlisted_valid(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.get('/shortlisted', follow_redirects=True)
    assert response.status_code == 200

def test_view_all_shortlisted_valid(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.get('/shortlisted', follow_redirects=True)
    assert response.status_code == 200

def test_toggle_shortlist_valid(client, login_user, test_job_experiences):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id

    # Assuming applicant ID is valid
    response = client.post(f'/shortlist/{test_job_experiences[0].id}/{login_user.id}')
    assert response.status_code == 302  # Redirect after success

def test_search_candidates_role_valid(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.post(
        '/search_candidates',
        data={
            'search_type': 'role',
            'search_query': 'Software Engineer'
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_search_candidates_skills_valid(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = True

    response = client.post(
        '/search_candidates',
        data={
            'search_type': 'skills',
            'search_query': 'Python'
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_search_candidates_unauthorized(client, login_user):
    with client.session_transaction() as session:
        session['user_id'] = login_user.id
        session['is_recruiter'] = False  # Simulate a non-recruiter user

    response = client.get('/search_candidates', follow_redirects=True)
    assert response.status_code == 200  # Redirected with unauthorized message

# Test "order applicants" as a non-recruiter
def test_order_applicants_unauthorized(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = False # Simulate a non-recruiter user

    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.get(f'/recruiter/order-applicants/{posting.postingId}', follow_redirects=True)
    assert response.status_code == 200 # Redirected with unauthorized message

# Test "order applicants" as a recruiter
def test_order_applicants_authorized(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True # Simulate a non-recruiter user

    # Add a posting
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.get(f'/recruiter/order-applicants/{posting.postingId}', follow_redirects=True)
    assert response.status_code == 200

# Test "order applicants" as a non-recruiter for an invalid posting id
def test_order_applicants_with_invalid_posting_id(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True # Recruiter

    # Add a posting
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.get('/recruiter/order-applicants/2', follow_redirects=True) # Expecting a 404 for postingId=2
    assert response.status_code == 404

# Test a new Posting with 0 applicants
def test_posting_with_no_applications(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True  # Recruiter
    
    # Add a posting
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    assert PostingApplications.query.filter_by(postingId=posting.postingId).all() == []

# Test "Order Applicants" for a posting with 0 applicants
def test_order_applicants_with_no_applications(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True  # Recruiter
    
    # Add a posting
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Software Engineer",
        jobLink="https://example.com/software-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    response = client.get(f'/recruiter/order-applicants/{posting.postingId}', follow_redirects=True)
    assert b'Applications are ordered' in response.data
    assert b'No applicants found for this job posting' in response.data

# Test "Order Applicants" for a posting with 1 applicant
def test_order_applicants_with_one_application(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True  # Recruiter
    
    # Add a posting
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Data Engineer",
        jobLink="https://example.com/data-engineer",
        jobDescription="Develop software applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )
    db.session.add(posting)
    db.session.commit()

    # Add a jobseeker
    jobseeker = User(username="test_user1", email="test1@example.com", password="testpasswd1")
    db.session.add(jobseeker)
    db.session.commit()

    # Add experiences for the jobseeker
    experiences = [
        JobExperience(
            job_title="Software Engineer",
            company_name="TechCorp",
            location="Remote",
            duration="2 years",
            description="Worked on web applications.",
            username=jobseeker.username
        ),
        JobExperience(
            job_title="Data Scientist",
            company_name="DataCorp",
            location="New York",
            duration="1 year",
            description="Analyzed large datasets.",
            username=jobseeker.username
        )
    ]
    db.session.add_all(experiences)
    db.session.commit()

    # Add an application by the jobseeker for the posting
    application = PostingApplications(
        postingId=posting.postingId,
        recruiterId=login_user.id,
        applicantId=jobseeker.id
    )
    db.session.add(application)
    db.session.commit()

    # Try ordering applicants in case of 1 applicant
    response = client.get(f'/recruiter/order-applicants/{posting.postingId}', follow_redirects=True)
    
    # Check the response
    assert b'Applications are ordered' in response.data
    assert b'test_user1' in response.data

# Check get_job_details in Recruiter_Postings
def test_get_job_details(client, login_user):
    with client.session_transaction() as session:
        session['_user_id'] = login_user.id
        session['is_recruiter'] = True

    # Add a sample posting with minimal values
    posting = Recruiter_Postings(
        postingId=1,
        recruiterId=login_user.id,
        jobTitle="Data Engineer",
        jobLink="https://example.com/data-engineer",
        jobDescription="Develop and maintain data engineering applications.",
        jobLocation="Remote",
        jobPayRate=50,
        maxHoursAllowed=40
    )

    db.session.add(posting)
    db.session.commit()

    # Test get_job_details
    expected_job_details = {
            'postingId': posting.postingId,
            'jobTitle': 'Data Engineer',
            'jobDescription': 'Develop and maintain data engineering applications.',
            'jobLocation': 'Remote'
        }

    assert posting.get_job_details() == expected_job_details

# Test Recommender with 0 application
def test_recommeder_for_posting_with_no_applications():
    # Empty list to imply no applications 
    application_user_profiles = []

    # Form the input prompt
    input_prompt = "Job Description: Data Engineer" + " \n " + json.dumps(application_user_profiles) + "\n Just give the output list."
    
    # Call GROQ AI API
    recommended_list = json.loads(call_groq_api("app\\prompts\\order_applicants_template.txt", input_prompt))

    assert recommended_list == []

# Test Recommender with 1 application
def test_recommender_for_posting_with_one_application():

    # List to imply one application 
    application_user_profiles = [
        {
            "job_title": ["SDE I", "SDE II"],
            "company_name": ["DataBricks", "Microsoft"],
            "duration": ["Jan 2019- Dec 2021", "Dec 2021 - Jun 2023"],
            "description": [
                "Worked in Big Data pipelines using Hadoop and Pyspark. Also built automated tests using Python.",
                "Worked in C# and Python based products. Also, worked in OneNote Team."
            ],
            "skills": ["PySpark, Hadoop", "C#, Python, SQL"],
            "username": "test_user1"
        }
    ]

    # Form the input prompt
    input_prompt = "Job Description: Data Engineer" + " \n " + json.dumps(application_user_profiles) + "\n Just give the output list."
    
    # Call GROQ AI API
    recommended_list = json.loads(call_groq_api("app\\prompts\\order_applicants_template.txt", input_prompt))

    assert recommended_list == [1]

# Test Recommeder with multiple applications
def test_recommeder_for_posting_with_multiple_applications():
    
    # List to imply multiple applications 
    application_user_profiles = [
        {
            "job_title": ["SDE I", "SDE II"],
            "company_name": ["DataBricks", "Microsoft"],
            "duration": ["Jan 2019- Dec 2021", "Dec 2021 - Jun 2023"],
            "description": [
                "Worked in Big Data pipelines using Hadoop and Pyspark. Also built automated tests using Python.",
                "Worked in C# and Python based products. Also, worked in OneNote Team."
            ],
            "skills": ["PySpark, Hadoop", "C#, Python, SQL"],
            "username": "test_user1"
        },
        {
            "job_title": ["SDE I", "SDE II"],
            "company_name": ["Amazon", "Meta"],
            "duration": ["Jan 2018- Jun 2022", "June 2022 - Present"],
            "description": [
            "Worked in AWS Website development.",
            "Worked in llama team."
            ],
            "skills": [
            "Java, Python, SQL, Spring Boot",
            "Python, NLP, LLM, OpenSource"
            ],
            "username": "test_user2"
        },
        {
            "job_title": ["QA I", "Senior QA ", "Lead QA"],
            "company_name": ["TCS", "YouTube", "YouTube"],
            "duration": [
            "Jan 2017 - May 2019",
            "July 2019 - Aug 2023",
            "September 2023 - Present"
            ],
            "description": [
            "Played a significant role in testing the Python Flask based webapp. Wrote automated tests.",
            "Worked on regression tests and automated tests for the Youtube wesite.",
            "Lead the QA team for Youtube website."
            ],
            "skills": [
            "Python, Flask, Postman, Selenium",
            "Python, Javascript, Selenium",
            "Python, Selenium, Project Management"
            ],
            "username": "test_user_3"
        }
    ]

    # Form the input prompt
    input_prompt = "Job Description: Senior QA Engineer for Python based app" + " \n " + json.dumps(application_user_profiles) + "\n Just give the output list."
    
    # Call GROQ AI API
    recommended_list = json.loads(call_groq_api("app\\prompts\\order_applicants_template.txt", input_prompt))

    assert recommended_list == [3, 1, 2]
