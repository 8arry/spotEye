#!/usr/bin/env python3
"""
SpotEye Notification Module
Handles email notifications for apartment changes
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List


class EmailNotifier:
    """Email notification service for apartment changes"""
    
    def __init__(self, config: Dict, logger: logging.Logger):
        """Initialize notifier with configuration and logger"""
        self.config = config
        self.logger = logger
        self.email_config = config['email']

    def send_notification(self, changes: List[Dict]):
        """Send email notification about apartment changes"""
        try:
            if not changes:
                self.logger.info("No changes to report, skipping email notification")
                return
            
            # Create email content
            subject = f"🏠 SpotEye Alert: {len(changes)} Apartment Updates Available!"
            html_content = self._create_email_content(changes)
            
            # Send email
            self._send_email(subject, html_content)
            
            self.logger.info(f"Successfully sent notification email for {len(changes)} changes")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def _create_email_content(self, changes: List[Dict]) -> str:
        """Create HTML email content for apartment changes"""
        
        new_apartments = [c for c in changes if c['type'] == 'new']
        status_changes = [c for c in changes if c['type'] == 'status_change']
        date_changes = [c for c in changes if c['type'] == 'date_change']
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
                .section {{ margin: 20px 0; }}
                .apartment {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #4CAF50; }}
                .apartment.new {{ border-left-color: #2196F3; }}
                .apartment.status {{ border-left-color: #FF9800; }}
                .apartment.date {{ border-left-color: #9C27B0; }}
                .details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px; }}
                .detail {{ background-color: white; padding: 8px; border-radius: 4px; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .urgent {{ background-color: #FFE0E0; border-left-color: #F44336 !important; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                .apply-link {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 SpotEye Apartment Monitor</h1>
                    <p>New apartment opportunities detected!</p>
                    <p>Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
        """
        
        # New apartments section
        if new_apartments:
            html_content += f"""
                <div class="section">
                    <h2>🆕 New Apartments ({len(new_apartments)})</h2>
            """
            
            for change in new_apartments:
                apt = change['apartment']
                urgent_class = 'urgent' if apt.get('availability') in ['available', 'soon'] else ''
                
                html_content += f"""
                    <div class="apartment new {urgent_class}">
                        <h3>Apartment {apt.get('id', 'N/A')} - {apt.get('type', 'Unknown')} Room</h3>
                        <div class="details">
                            <div class="detail">
                                <div class="label">Floor:</div>
                                <div class="value">{apt.get('floor', 'N/A')}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Location:</div>
                                <div class="value">{apt.get('location', 'N/A')}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Size:</div>
                                <div class="value">{apt.get('size', 'N/A')} m²</div>
                            </div>
                            <div class="detail">
                                <div class="label">Price:</div>
                                <div class="value">€{apt.get('price', 'N/A')}/month</div>
                            </div>
                            <div class="detail">
                                <div class="label">Balcony:</div>
                                <div class="value">{apt.get('balcony', 'N/A').title()}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Status:</div>
                                <div class="value">{apt.get('availability', 'N/A').title()}</div>
                            </div>
                        </div>
                        {f'<div style="margin-top: 10px;"><strong>Available from: {apt.get("available_date")}</strong></div>' if apt.get('available_date') else ''}
                        {f'<div style="margin-top: 5px; color: #4CAF50;"><strong>✅ Barrier-free accessible</strong></div>' if apt.get('barrier_free') else ''}
                        <a href="https://www.apartments-hn.de/en/book-apartment" class="apply-link">View on Website</a>
                    </div>
                """
            
            html_content += "</div>"
        
        # Status changes section
        if status_changes:
            html_content += f"""
                <div class="section">
                    <h2>📈 Availability Changes ({len(status_changes)})</h2>
            """
            
            for change in status_changes:
                apt = change['apartment']
                old_status = change['old_status']
                new_status = change['new_status']
                urgent_class = 'urgent' if new_status in ['available', 'soon'] else ''
                
                html_content += f"""
                    <div class="apartment status {urgent_class}">
                        <h3>Apartment {apt.get('id', 'N/A')} - Status Updated!</h3>
                        <p><strong>Status changed: {old_status.title()} → {new_status.title()}</strong></p>
                        <div class="details">
                            <div class="detail">
                                <div class="label">Type:</div>
                                <div class="value">{apt.get('type', 'N/A')}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Location:</div>
                                <div class="value">{apt.get('location', 'N/A')}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Price:</div>
                                <div class="value">€{apt.get('price', 'N/A')}/month</div>
                            </div>
                        </div>
                        {f'<div style="margin-top: 10px;"><strong>Available from: {apt.get("available_date")}</strong></div>' if apt.get('available_date') else ''}
                        <a href="https://www.apartments-hn.de/en/book-apartment" class="apply-link">Check Now</a>
                    </div>
                """
            
            html_content += "</div>"
        
        # Date changes section
        if date_changes:
            html_content += f"""
                <div class="section">
                    <h2>📅 Date Updates ({len(date_changes)})</h2>
            """
            
            for change in date_changes:
                apt = change['apartment']
                old_date = change['old_date'] or 'Not specified'
                new_date = change['new_date']
                
                html_content += f"""
                    <div class="apartment date">
                        <h3>Apartment {apt.get('id', 'N/A')} - Date Updated!</h3>
                        <p><strong>Available date: {old_date} → {new_date}</strong></p>
                        <div class="details">
                            <div class="detail">
                                <div class="label">Type:</div>
                                <div class="value">{apt.get('type', 'N/A')}</div>
                            </div>
                            <div class="detail">
                                <div class="label">Location:</div>
                                <div class="value">{apt.get('location', 'N/A')}</div>
                            </div>
                        </div>
                        <a href="https://www.apartments-hn.de/en/book-apartment" class="apply-link">View Details</a>
                    </div>
                """
            
            html_content += "</div>"
        
        html_content += f"""
                <div class="footer">
                    <p>🤖 This message was sent automatically by SpotEye</p>
                    <p>Monitoring: <a href="https://www.apartments-hn.de/en/book-apartment">W|27 German Student Apartments</a></p>
                    <p><small>To stop receiving these notifications, please contact your system administrator.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _send_email(self, subject: str, html_content: str):
        """Send email using Gmail SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['smtp_user']
            msg['To'] = self.email_config['recipient_email']
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()  # Enable encryption
            server.login(self.email_config['smtp_user'], self.email_config['smtp_password'])
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.email_config['smtp_user'], self.email_config['recipient_email'], text)
            server.quit()
            
            self.logger.info("Email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    def send_test_notification(self):
        """Send a test notification to verify email configuration"""
        try:
            subject = "🧪 SpotEye Test Notification"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
                    .content {{ text-align: center; padding: 20px; }}
                    .footer {{ text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🧪 SpotEye Test</h1>
                        <p>Email Configuration Test</p>
                    </div>
                    <div class="content">
                        <h2>✅ Email System Working!</h2>
                        <p>This is a test message to verify that your SpotEye email notification system is properly configured.</p>
                        <p><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>If you received this message, your email notifications are ready to go!</p>
                    </div>
                    <div class="footer">
                        <p>🤖 SpotEye Apartment Monitor</p>
                        <p><small>This is an automated test message.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self._send_email(subject, html_content)
            self.logger.info("Test notification sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send test notification: {e}")
            return False 