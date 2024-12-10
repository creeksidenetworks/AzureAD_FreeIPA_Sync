#!/usr/bin/env python
# Azure AD user/group FreeIPA sync utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import src.logger

def send_email(server, port, user, password, subject, body, recipients):
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

    # Create HTML part
    html_body = f"""
    <html>
    <head></head>
    <body>
        <pre style="font-family: Courier, monospace;">
        {body}
        </pre>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(server, port)
        server.starttls()
        server.login(user, password)
        text = msg.as_string()
        server.sendmail(user, recipients, text)
        server.quit()
        src.logger.logger.info("Email sent successfully")
    except Exception as e:
        src.logger.logger.error(f"Failed to send email: {e}")