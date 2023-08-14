def send_magic_link_email(user, link):
    """Send an email with this login link to this user."""
    user.email_user(
        subject="[Turboprop] Log in to our app",
        from_email="hello@turboprop.ai",
        message=f"""\
Hello,

You requested that we send you a link to log in to our app:

    {link}

Thank you for using Turboprop!
""",
    )
