"""
Email Service
=============
Handles email sending for various notification types.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.core.logger import logger


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.template_dir = "configs/email/templates"
        self.template_env = Environment(
            loader=FileSystemLoader(self.template_dir)
        )
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render email template with data."""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return f"<p>Email content could not be rendered. Please check your inbox.</p>"
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email via SMTP."""
        if not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email send")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg["To"] = to_email
            
            # Add plain text version
            if text_content:
                part_text = MIMEText(text_content, "plain")
                msg.attach(part_text)
            
            # Add HTML version
            part_html = MIMEText(html_content, "html")
            msg.attach(part_html)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """Send welcome email to new user."""
        html_content = self._render_template("welcome.html", template_data)
        return self._send_email(
            to_email=to_email,
            subject=f"Welcome to Abdulboy Ebook Empire, {template_data.get('name', 'Reader')}! 📚",
            html_content=html_content
        )
    
    def send_purchase_confirmation(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """Send purchase confirmation email."""
        html_content = self._render_template("purchase-confirmation.html", template_data)
        return self._send_email(
            to_email=to_email,
            subject=f"Purchase Confirmation - Order #{template_data.get('orderId', 'N/A')}",
            html_content=html_content
        )
    
    def send_password_reset_email(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """Send password reset email."""
        html_content = self._render_template("password-reset.html", template_data)
        return self._send_email(
            to_email=to_email,
            subject="Reset Your Password - Abdulboy Ebook Empire",
            html_content=html_content
        )
    
    def send_booking_confirmation(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """Send custom book booking confirmation."""
        html_content = self._render_template("booking-received.html", template_data)
        return self._send_email(
            to_email=to_email,
            subject=f"Custom Book Request Received - #{template_data.get('bookingId', 'N/A')}",
            html_content=html_content
        )
    
    def send_booking_update(self, to_email: str, template_data: Dict[str, Any]) -> bool:
        """Send booking status update email."""
        # Use booking-received template with status context
        html_content = self._render_template("booking-received.html", template_data)
        return self._send_email(
            to_email=to_email,
            subject=f"Update on Your Custom Book Request - #{template_data.get('bookingId', 'N/A')}",
            html_content=html_content
        )
    
    def send_daily_report(self, to_email: str, report_data: Dict[str, Any]) -> bool:
        """Send daily analytics report."""
        # Create simple report email
        html_content = f"""
        <html>
        <body>
            <h1>Daily Analytics Report</h1>
            <p>Date: {report_data.get('date', 'N/A')}</p>
            <ul>
                <li>New Users: {report_data.get('new_users', 0)}</li>
                <li>New Books: {report_data.get('new_books', 0)}</li>
                <li>Revenue: ${report_data.get('revenue', 0):.2f}</li>
                <li>Active Users: {report_data.get('active_users', 0)}</li>
            </ul>
        </body>
        </html>
        """
        return self._send_email(
            to_email=to_email,
            subject=f"Daily Report - {report_data.get('date', 'N/A')}",
            html_content=html_content
        )
    
    def send_weekly_report(self, to_email: str, report_data: Dict[str, Any]) -> bool:
        """Send weekly analytics report."""
        # Create simple report email
        top_books_html = ""
        for book in report_data.get('top_books', [])[:5]:
            top_books_html += f"<li>{book.get('title')} - {book.get('downloads')} downloads</li>"
        
        html_content = f"""
        <html>
        <body>
            <h1>Weekly Analytics Report</h1>
            <p>Period: {report_data.get('period_start', 'N/A')} to {report_data.get('period_end', 'N/A')}</p>
            <ul>
                <li>New Users: {report_data.get('new_users', 0)}</li>
                <li>New Books: {report_data.get('new_books', 0)}</li>
                <li>Revenue: ${report_data.get('revenue', 0):.2f}</li>
            </ul>
            <h3>Top Books</h3>
            <ul>{top_books_html}</ul>
        </body>
        </html>
        """
        return self._send_email(
            to_email=to_email,
            subject=f"Weekly Report - Week Ending {report_data.get('period_end', 'N/A')}",
            html_content=html_content
        )
    
    def send_monthly_report(self, to_email: str, report_data: Dict[str, Any]) -> bool:
        """Send monthly analytics report."""
        html_content = f"""
        <html>
        <body>
            <h1>Monthly Analytics Report</h1>
            <p>Period: {report_data.get('period_start', 'N/A')} to {report_data.get('period_end', 'N/A')}</p>
            <ul>
                <li>Total Users: {report_data.get('total_users', 0)}</li>
                <li>New Users: {report_data.get('new_users', 0)}</li>
                <li>Active Subscribers: {report_data.get('active_subscribers', 0)}</li>
                <li>Revenue: ${report_data.get('revenue', 0):.2f}</li>
                <li>User Retention: {report_data.get('user_retention', 0):.1f}%</li>
            </ul>
        </body>
        </html>
        """
        return self._send_email(
            to_email=to_email,
            subject=f"Monthly Report - {report_data.get('period_end', 'N/A')}",
            html_content=html_content
        )
