import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Sequence

from domainwizard.config import config
from domainwizard.models import DomainSearch, Listing
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

env = Environment(loader=PackageLoader("domainwizard"), autoescape=select_autoescape())

email_template = env.get_template("updates.html.jinja2")


def send_update_email(domain_search: DomainSearch, listings: Sequence[Listing]):
    if domain_search.email is None:
        raise ValueError("Domain search email is None")

    # Render template
    html_content = email_template.render(domain_search=domain_search, updated_listings=listings)

    # Create message
    message = MIMEMultipart()
    message["From"] = config["EMAIL_FROM"]
    message["To"] = domain_search.email
    message["Subject"] = "urlwiz.io - Your new domain name suggestions"

    # Attach HTML content
    message.attach(MIMEText(html_content, "html"))

    # Send email
    logger.info(f"Sending update email to {domain_search.email}")
    with smtplib.SMTP(config["SMTP_SERVER"], 587) as server:
        server.starttls()
        server.login(config["EMAIL_FROM"], config["EMAIL_PASSWORD"])
        server.send_message(message)
