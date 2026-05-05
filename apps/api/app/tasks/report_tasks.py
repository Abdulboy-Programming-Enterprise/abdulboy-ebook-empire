"""
Report Tasks
============
Celery tasks for generating analytics reports.
"""

from celery import shared_task
from datetime import datetime, timedelta
from app.services.analytics.service import AnalyticsService
from app.services.notifications.email_service import EmailService
from app.core.database import SessionLocal
from app.core.logger import logger


@shared_task(name="generate_daily_report")
def generate_daily_report():
    """
    Generate and send daily analytics report.
    """
    try:
        db = SessionLocal()
        analytics = AnalyticsService(db)
        email_service = EmailService()
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Generate report data
        report_data = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "new_users": analytics.get_new_users_count(yesterday),
            "new_books": analytics.get_new_books_count(yesterday),
            "revenue": analytics.get_daily_revenue(yesterday),
            "active_users": analytics.get_active_users_count(yesterday),
        }
        
        # Send to admin email
        email_service.send_daily_report(
            to_email="admin@abdulboy-ebook.com",
            report_data=report_data
        )
        
        logger.info(f"Daily report sent for {yesterday.date()}")
        db.close()
        
        return {"status": "success", "report_data": report_data}
        
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="generate_weekly_report")
def generate_weekly_report():
    """
    Generate and send weekly analytics report.
    """
    try:
        db = SessionLocal()
        analytics = AnalyticsService(db)
        email_service = EmailService()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        report_data = {
            "period_start": week_ago.strftime("%Y-%m-%d"),
            "period_end": datetime.utcnow().strftime("%Y-%m-%d"),
            "new_users": analytics.get_new_users_count(week_ago),
            "new_books": analytics.get_new_books_count(week_ago),
            "revenue": analytics.get_period_revenue(week_ago),
            "top_books": analytics.get_top_books(limit=10),
            "top_categories": analytics.get_top_categories(limit=5),
        }
        
        email_service.send_weekly_report(
            to_email="admin@abdulboy-ebook.com",
            report_data=report_data
        )
        
        logger.info("Weekly report sent")
        db.close()
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        return {"status": "error", "error": str(e)}


@shared_task(name="generate_monthly_report")
def generate_monthly_report():
    """
    Generate and send monthly analytics report.
    """
    try:
        db = SessionLocal()
        analytics = AnalyticsService(db)
        email_service = EmailService()
        
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        report_data = {
            "period_start": month_ago.strftime("%Y-%m-%d"),
            "period_end": datetime.utcnow().strftime("%Y-%m-%d"),
            "new_users": analytics.get_new_users_count(month_ago),
            "new_books": analytics.get_new_books_count(month_ago),
            "revenue": analytics.get_period_revenue(month_ago),
            "total_users": analytics.get_total_users(),
            "active_subscribers": analytics.get_active_subscribers_count(),
            "top_books": analytics.get_top_books(limit=20),
            "top_categories": analytics.get_top_categories(limit=10),
            "user_retention": analytics.get_user_retention_rate(),
        }
        
        email_service.send_monthly_report(
            to_email="admin@abdulboy-ebook.com",
            report_data=report_data
        )
        
        logger.info("Monthly report sent")
        db.close()
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to generate monthly report: {e}")
        return {"status": "error", "error": str(e)}
