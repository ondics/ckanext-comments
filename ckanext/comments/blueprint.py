import ckan.lib.mailer as mailer
import ckan.plugins.toolkit as toolkit
import uuid
from flask import Flask, request, jsonify, render_template, Blueprint, session
import re
import random
import logging
from ckan.views.user import _extra_template_variables
from ckan.lib.helpers import helper_functions as h
from ckan import model
from ckanext.comments.model import Comment
import json

log = logging.getLogger(__name__)

blueprint = Blueprint(u'comments_blueprint', __name__)

def request_pin():
    data = request.json
    email = data.get('email')

    user = toolkit.g.userobj
    if user:
        author_id = user.id
        author_name = user.name
    else: 
        author_id = data.get('name')
        author_name = data.get('name')

    if not is_valid_email(email):
        return jsonify({"error": "Ungültige E-Mail-Adresse."}), 400

    pin = generate_pin()
    session['confirmation_pin'] = {
        'email': email,
        'pin': pin
    }

    # Erstelle den Bestätigungslink
    my_url = toolkit.config.get("ckan.site_url")

    # Sende die Bestätigungsmail
    subject = (f"{author_name} - Bestätigen Sie Ihre E-Mail-Adresse")
    body = f"Bitte geben Sie die folgende PIN ein, um Ihre E-Mail-Adresse zu bestätigen und Ihren Kommentar zu speichern: {pin}"
    body_html = body

    try:
        mailer.mail_recipient(
            author_name,
            email,
            subject,
            body,
            body_html = body_html
            )
    except mailer.MailerException as e:
        h.flash_error(toolkit._(u'Error sending the email. Try again later '
                        'or contact an administrator for help'))
        log.exception(e)

    return jsonify({"message": "Bestätigungscode wurde gesendet."})

def verify_pin():
    data = request.json
    email = data.get('email')
    entered_pin = data.get('pin')

    confirmation_data = session.get('confirmation_pin')
    if not confirmation_data or confirmation_data['email'] != email:
        return jsonify({"error": "Ungültige oder abgelaufene Anfrage."}), 400

    if confirmation_data['pin'] != entered_pin:
        return jsonify({"error": "Ungültiger PIN."}), 400

    session.pop('confirmation_pin', None)  # Entferne PIN aus der Session
    return jsonify({"message": "PIN bestätigt."})

def is_valid_email(email):
    # Einfacher Regex für E-Mail-Validierung
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def generate_pin():
    """Generiere eine 6-stellige PIN."""
    return f"{random.randint(100000, 999999)}"

def check_guest_user():
    data = request.get_json()
    guest_user = data.get('guest_user')
    author_email = data.get('author_email')


    if not guest_user or not author_email:
        return jsonify({'valid': False, 'error': 'Missing data'}), 400

    # Finde alle Einträge mit diesem Gastnamen
    existing = model.Session.query(Comment).filter_by(author_type='guest', guest_user=guest_user).all()

    for comment in existing:
        if comment.author_email != author_email:
            # Derselbe Benutzername wurde mit einer anderen E-Mail verwendet
            return jsonify({'valid': False, 'error': 'Dieser Gastname ist bereits mit einer anderen E-Mail-Adresse verbunden.'}), 409

    # Entweder existiert der Name noch nicht oder nur mit derselben E-Mail
    return jsonify({'valid': True}), 200

def dashboard_comments():
    context = {u'for_view': True, u'user': toolkit.g.user, u'auth_user_obj': toolkit.g.userobj}
    data_dict = {u'user_obj': toolkit.g.userobj}
    extra_vars = _extra_template_variables(context, data_dict)
    try:
        toolkit.check_access('sysadmin', context, data_dict)
    except toolkit.NotAuthorized:
        return toolkit.abort(403, toolkit._('User not authorized to view page'))
    
    return toolkit.render("/user/dashboard_comments.html", extra_vars)


blueprint.add_url_rule('/dashboard/comments',
              view_func=dashboard_comments)

blueprint.add_url_rule('/api/request_pin',
              view_func=request_pin, methods=['POST'])

blueprint.add_url_rule('/api/verify_pin',
              view_func=verify_pin, methods=['POST'])

blueprint.add_url_rule('/api/check_guest_user',
              view_func=check_guest_user, methods=['POST'])

def get_blueprints():
    return [blueprint]