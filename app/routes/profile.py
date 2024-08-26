from flask import Blueprint
from routes.imports import *
from routes.auth import login_required
from config import *

profile_bp=Blueprint("profile",__name__)


@profile_bp.route('/profile')
@login_required
def profile():
    user = session['user']
    # print(user)
    return render_template('profile.html', user=user)


@profile_bp.route('/edit-profile', methods=['POST'])
def edit_profile():
    email = request.cookies.get('user_email')
    if not email:
        return redirect(url_for('login'))

    full_name = request.form.get('full_name')
    new_email = request.form.get('email')

    session['user']['full_name'] = full_name
    session['user']['email'] = new_email

    update_payload = {
        "fullName": full_name,
        "email": new_email,
    }

    try:
        # PUT request to update the trainee details by email
        response = requests.put(f"{base_url_company_user}{
                                email}", json=update_payload)
        response.raise_for_status()

        flash('Profile updated successfully', 'success')

        # Update the session cookies
        response = make_response(redirect(url_for('profile')))
        response.set_cookie('user_email', new_email,
                            secure=True, httponly=True)
        response.set_cookie('user_full_name', full_name,
                            secure=True, httponly=True)

        return response

    except requests.RequestException as e:
        flash(f"Failed to update profile: {e}", 'error')
        return redirect(url_for('profile'))
