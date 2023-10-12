"""
Settings and functions for e-mail(smtp) reporting
"""

from datetime import datetime
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ssl import create_default_context, OPENSSL_VERSION
from email.message import EmailMessage


# SIMPLE SEND EMAIL FUNCTION W/WO AUTH
def send_mail(mail_to, mail_from, smtp_server, smtp_port, mail_data, subject='TEST EMAIL', login=None, password=None):
    """
    Simple email send, using 25(SMTP without auth) or 587(TLS, with auth) ports.
    Use Auth method(starttls()) if login & password are present.
    Sender(mail_to may be list or single sender.

    Args:
        mail_to: list or tuple(for several emails) or str for single address
        mail_from: str, mail from field
        smtp_server: str, server ip/name
        smtp_port: int/str, server's port
        mail_data: str, mail body
        subject: str, mail subject
        login: str, login
        password: str, password
    """
    with SMTP(smtp_server, smtp_port) as server:
        # DEBUG: 1 or 2(with timestamp)
        # print(OPENSSL_VERSION)
        # server.set_debuglevel(1)

        # USE AUTH: STARTTLS IF LOGIN & PASS IS NOT NONE
        if login and password:
            context = create_default_context()
            server.starttls(context=context)
            server.login(login, password)
        # message = MIMEMultipart()

        message = EmailMessage()
        message.set_content(mail_data, subtype='html')

        message["From"] = mail_from
        message["Subject"] = subject
        if isinstance(mail_to, (list, tuple)):
            message["To"] = ', '.join(mail_to)
        else:
            message["To"] = mail_to
        # message.attach(MIMEText(mail_data, "html"))
        # data = message.as_string()
        # server.sendmail(mail_from, mail_to, data)

        server.send_message(message, mail_from, mail_to)

        server.quit()
    return True


# EMAIL REPORT W/WO AUTH
def send_mail_report(appname, mail_to, mail_from, smtp_server, smtp_port,
                     log_file=None, mail_body=None,login=None, password=None,):
    """
    To send email report at.
    By default, at the end of the script only.
    Use Auth method(starttls()) if login & password are present.
    Sender(mail_to may be list or single sender.
    If log_file presents: send log file.
    If only mail_body presents: send mail_body
    If both log_file & mail_bcdy presents send only log_file.

    Args:
        appname: str, your app name
        mail_to: list or tuple(for several emails) or str for single address
        mail_from: str, mail from field
        smtp_server: str, server ip/name
        smtp_port: int/str, server's port
        log_file: None by default, any text file
        mail_body: None by default, str
        login: str, login
        password: str, password
    """
    message = MIMEMultipart()
    message["From"] = mail_from
    message["Subject"] = f'{appname} - Script Report({datetime.now()})'
    if isinstance(mail_to, (list, tuple)):
        message["To"] = ', '.join(mail_to)
    else:
        message["To"] = mail_to

    if log_file:
        with open(log_file, 'r') as log:
            report = log.read()
            message.attach(MIMEText(report, "plain"))
    elif mail_body:
        message.attach(MIMEText(mail_body, "plain"))
    else:
        raise Exception('NEITHER LOG_FILE NOR MAIL_BODY PRESENTS')
    with SMTP(smtp_server, smtp_port) as server:
        # DEBUG: 1 or 2(with timestamp)
        # server.set_debuglevel(1)

        # USE AUTH: STARTTLS IF LOGIN IS NOT NONE
        if login and password:
            context = create_default_context()
            server.starttls(context=context)  # Secure the connection
            server.login(login, password)
        data = message.as_string()
        server.sendmail(mail_from, mail_to, data)
        server.quit()
    return True
