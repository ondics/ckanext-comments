from datetime import datetime

import ckan.lib.dictization as d
import ckan.plugins.toolkit as tk
from ckan.logic import validate
import ckan.authz as authz
import ckan.lib.helpers as h

import ckanext.comments.logic.schema as schema
from ckanext.comments.model import Comment, Thread
from ckanext.comments.model.dictize import get_dictizer

from ckan.model import Session

from .. import config, signals

import logging

log = logging.getLogger(__name__)

_actions = {}


def action(func):
    func.__name__ = f"comments_{func.__name__}"
    _actions[func.__name__] = func
    return func


def get_actions():
    return _actions.copy()


@action
@validate(schema.thread_create)
def thread_create(context, data_dict):
    """Create a thread for the subject.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity

    """
    tk.check_access("comments_thread_create", context, data_dict)

    thread = Thread.for_subject(
        data_dict["subject_type"], data_dict["subject_id"], init_missing=True
    )

    if thread.id:
        raise tk.ValidationError(
            {"id": ["Thread for the given subject_id and subject_type already exists"]}
        )
    if thread.get_subject() is None:
        raise tk.ObjectNotFound("Cannot find subject for thread")

    context["session"].add(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_show)
def thread_show(context, data_dict):
    """Show the subject's thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        init_missing(bool, optional): return an empty thread instead of 404
        include_comments(bool, optional): show comments from the thread
        include_author(bool, optional): show authors of the comments
        combine_comments(bool, optional): combine comments into a tree-structure
        after_date(str:ISO date, optional): show comments only since the given date
    """
    tk.check_access("comments_thread_show", context, data_dict)
    thread = Thread.for_subject(
        data_dict["subject_type"],
        data_dict["subject_id"],
        init_missing=data_dict["init_missing"],
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")

    context["include_comments"] = data_dict["include_comments"]
    context["combine_comments"] = data_dict["combine_comments"]
    context["include_author"] = data_dict["include_author"]
    context["after_date"] = data_dict.get("after_date")

    context["newest_first"] = data_dict["newest_first"]

    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_delete)
def thread_delete(context, data_dict):
    """Delete the thread.

    Args:
        id(str): ID of the thread
    """
    tk.check_access("comments_thread_delete", context, data_dict)
    thread = (
        context["session"]
        .query(Thread)
        .filter(Thread.id == data_dict["id"])
        .one_or_none()
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")

    context["session"].delete(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


def update_guest_user_if_needed(data_dict):
    '''
    Überprüft guest user auf Einzigartigkeit.
    Kommentar wird nicht erstellt, falls bereits ein guest user mit dem eingegebenen Namen 
    und unterschiedlicher Autor-Email in der Datenbanktabelle vorhanden sind.
    '''
    if data_dict.get('author_type') != 'guest':
        return

    email = data_dict.get('author_email')
    new_guest_user = data_dict.get('guest_user')
    if not email or not new_guest_user:
        return

    # Finde bisherigen Kommentar mit derselben Email
    existing_comment = (
        Session.query(Comment)
        .filter_by(author_email=email, author_type='guest')
        .first()
    )

    if existing_comment and existing_comment.guest_user != new_guest_user:
        # Update alle bisherigen Kommentare auf den neuen Namen
        Session.query(Comment)\
            .filter_by(author_email=email, author_type='guest')\
            .update({Comment.guest_user: new_guest_user})
        Session.commit()

@action
@validate(schema.comment_create)
def comment_create(context, data_dict):
    """Add a comment to the thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        content(str): comment's message
        reply_to_id(str, optional): reply to the existing comment
        create_thread(bool, optional): create a new thread if it doesn't exist yet
    """
    tk.check_access("comments_comment_create", context, data_dict)

    if authz.auth_is_anon_user(context):
        data_dict["author_type"] = "guest"
    else:
        data_dict["author_type"] = "user"

    thread_data = {
        "subject_id": data_dict["subject_id"],
        "subject_type": data_dict["subject_type"],
    }
    try:
        thread_dict = tk.get_action("comments_thread_show")(context.copy(), thread_data)
    except tk.ObjectNotFound:
        if not data_dict["create_thread"]:
            raise
        thread_dict = tk.get_action("comments_thread_create")(
            context.copy(), thread_data
        )

    author_id = data_dict.get("author_id")
    guest_user = data_dict.get("guest_user")
    auth_user = context.get("auth_user_obj")
    ignore_auth = context.get("ignore_auth", False)

    can_set_author_id = ignore_auth or (auth_user and getattr(auth_user, "sysadmin", False))

    if not author_id or not can_set_author_id:
        author_id = context["user"]

    reply_to_id = data_dict.get("reply_to_id")
    if reply_to_id:
        parent = tk.get_action("comments_comment_show")(
            context.copy(), {"id": reply_to_id}
        )
        if parent["thread_id"] != thread_dict["id"]:
            raise tk.ValidationError(
                {"reply_to_id": ["Comment is owned by different thread"]}
            )
    if authz.auth_is_anon_user(context):
        data_dict["author_type"] = "guest"
    else:
        data_dict["author_type"] = "user"
        author = authz._get_user(author_id)
        data_dict["author_email"] = author.email

    author_email = data_dict["author_email"]
    author_type = data_dict["author_type"]

    comment = Comment(
        thread_id=thread_dict["id"],
        content=data_dict["content"],
        author_email=author_email,
        author_type=author_type,
        extras=data_dict["extras"],
        author_id=author_id,
        guest_user=guest_user,
        reply_to_id=reply_to_id,
    )

    # make sure we are not messing up with name_or_id
    if comment.author_type == "user":
        author = comment.get_author()
        if author is None:
            raise tk.ObjectNotFound("Cannot find author for comment")
        comment.author_id = author.id
        comment.guest_user = None  # Gästename darf nicht gesetzt sein, wenn es ein User ist
    else:
        comment.author_id = None  # Keine User-ID setzen, wenn es ein Gast ist
        comment.guest_user = guest_user or data_dict.get("guest_user")

    if author_type == 'guest' and guest_user and author_email:
        # Suche, ob der guest_user schon existiert – mit anderer Email
        existing = Session.query(Comment)\
            .filter(Comment.guest_user == guest_user)\
            .filter(Comment.author_email != author_email)\
            .filter(Comment.author_type == 'guest')\
            .first()

        if existing:
            # Username ist mit einer anderen Email belegt
            h.flash_error("Der angegebene Gastautor wird bereits verwendet. Bitte verwenden Sie einen anderen Namen.")
            return
    
    update_guest_user_if_needed(data_dict)

    if not config.approval_required():
        comment.approve()
    context["session"].add(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.created.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_show)
def comment_show(context, data_dict):
    """Show the details of the comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_show", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment_dict = get_dictizer(type(comment))(comment, context)
    return comment_dict


@action
@validate(schema.comment_approve)
def comment_approve(context, data_dict):
    """Approve draft comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_approve", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.approve()
    context["session"].commit()

    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.approved.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_delete)
def comment_delete(context, data_dict):
    """Remove existing comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_delete", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")

    context["session"].delete(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.deleted.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_update)
def comment_update(context, data_dict):
    """Update existing comment

    Args:
        id(str): ID of the comment
        content(str): comment's message
    """

    tk.check_access("comments_comment_update", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )

    if comment is None:
        raise tk.ObjectNotFound("Comment not found")

    comment.content = data_dict["content"]
    comment.modified_at = datetime.utcnow()
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.updated.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
def comment_list(context, data_dict):
    """Show list of draft comments"""

    # tk.check_access("comments_comment_show", context, data_dict)
    comments = (
        context["session"]
        .query(Comment, Thread.subject_id)
        .join(Thread, Comment.thread_id == Thread.id)
        .filter(Comment.state == data_dict["state"])
        .all()
    )

    comments_list = []

    comments_list = [
        {
            **get_dictizer(type(comment))(comment, context),
            'package_id': subject_id,
            'author_name': (
                tk.get_action('user_show')(data_dict={'id': comment.author_id}).get('name')
                if comment.author_id else comment.guest_user or "Gast"
            ),
            'author_fullname': (
                tk.get_action('user_show')(data_dict={'id': comment.author_id}).get('fullname')
                if comment.author_id else comment.guest_user or "Gast"
            ),
        }
        for comment, subject_id in comments
    ]

    return comments_list