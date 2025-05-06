import os
import json
import logging
import tempfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEETS_URL, GOOGLE_SHEETS_CREDENTIALS

# Initialize logger
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Manager for Google Sheets operations."""
    
    def __init__(self):
        """Initialize the Google Sheets connection."""
        self._client = None
        self._spreadsheet = None
        self._worksheets = {}
        
    def _get_worksheet(self, name, create_if_missing=True):
        """Get a specific worksheet by name, creating it if it doesn't exist."""
        # Connect to sheets if not already connected
        if not self._spreadsheet:
            self._connect_to_sheets()
            
        # Check if we have the worksheet cached
        if name in self._worksheets:
            return self._worksheets[name]
            
        # Try to find the worksheet
        try:
            worksheet = self._spreadsheet.worksheet(name)
            self._worksheets[name] = worksheet
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            if create_if_missing:
                # Create a new worksheet
                worksheet = self._spreadsheet.add_worksheet(title=name, rows=100, cols=20)
                
                # Add headers based on worksheet type
                if name == "attendance":
                    worksheet.append_row(["User ID", "Username", "Action", "Timestamp"])
                elif name == "students":
                    worksheet.append_row(["ID", "Registered By", "Name", "Phone", "Subject", "Timestamp"])
                elif name == "payments":
                    worksheet.append_row(["Recorded By", "Student ID", "Payment Date", "Amount", "Timestamp"])
                
                self._worksheets[name] = worksheet
                logger.info(f"Created new worksheet: {name}")
                return worksheet
            else:
                raise
    
    def _connect_to_sheets(self):
        """Connect to Google Sheets using service account credentials."""
        try:
            # Define the scope
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Check if we have credentials in environment variable
            temp_creds_path = None
            use_temp_file = False
            
            # Try to use environment variable first
            if GOOGLE_SHEETS_CREDENTIALS:
                logger.info("Found Google Sheets credentials in environment variables")
                
                # Create a temporary file with the credentials JSON string
                try:
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
                        try:
                            f.write(GOOGLE_SHEETS_CREDENTIALS)
                            temp_creds_path = f.name
                            use_temp_file = True
                        except TypeError:
                            logger.error("Google Sheets credentials format issue - must be a valid JSON string")
                except Exception as e:
                    logger.error(f"Error creating temp file for credentials: {e}")
            
            # Fall back to credentials.json file if environment variable didn't work
            if not use_temp_file:
                logger.info("Using credentials.json file as fallback")
                temp_creds_path = "credentials.json"
                if not os.path.exists(temp_creds_path):
                    raise ValueError("No valid credentials found. Please provide GOOGLE_SHEETS_CREDENTIALS or ensure credentials.json exists.")
                
            try:
                # Get credentials from the temporary file
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    temp_creds_path, scope
                )
                
                # Authorize with Google
                self._client = gspread.authorize(creds)
                
                # Open the spreadsheet by URL
                self._spreadsheet = self._client.open_by_url(GOOGLE_SHEETS_URL)
                
                # Reset worksheets cache
                self._worksheets = {}
                
                logger.info("Successfully connected to Google Sheets")
            finally:
                # Delete the temporary file to keep credentials secure
                if use_temp_file and os.path.exists(temp_creds_path):
                    os.unlink(temp_creds_path)
                    
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise
    
    def record_attendance(self, user_id, username, action, timestamp):
        """Record attendance in the Google Sheet.
        
        Args:
            user_id (str): The Telegram user ID
            username (str): The Telegram username or first name
            action (str): The action taken (e.g., "Davomat")
            timestamp (str): The timestamp of the action
        """
        try:
            # Get the attendance worksheet
            worksheet = self._get_worksheet("attendance")
            
            # Append a new row to the sheet
            worksheet.append_row([user_id, username, action, timestamp])
            logger.info(f"Recorded attendance for user {user_id} ({username})")
        except Exception as e:
            logger.error(f"Failed to record attendance: {e}")
            # Attempt to reconnect and try again
            self._connect_to_sheets()
            try:
                worksheet = self._get_worksheet("attendance")
                worksheet.append_row([user_id, username, action, timestamp])
                logger.info(f"Successfully recorded attendance after reconnection for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to record attendance after reconnection: {e}")
                raise
                
    def record_student(self, registered_by, name, phone, subject, timestamp):
        """Record a new student in the Google Sheet.
        
        Args:
            registered_by (str): The Telegram user ID who registered the student
            name (str): The student's full name
            phone (str): The student's phone number
            subject (str): The subject the student is studying
            timestamp (str): The timestamp of registration
        """
        try:
            # Get the students worksheet
            worksheet = self._get_worksheet("students")
            
            # Generate a unique ID for the student
            all_values = worksheet.get_all_values()
            rows = len(all_values)
            
            # Skip the header row when counting
            if rows > 0:
                student_id = str(rows)  # Simple sequential ID
            else:
                student_id = "1"  # First student
                
            # Append a new row to the sheet
            worksheet.append_row([student_id, registered_by, name, phone, subject, timestamp])
            logger.info(f"Recorded new student: {name} with ID {student_id}")
            
        except Exception as e:
            logger.error(f"Failed to record student: {e}")
            # Attempt to reconnect and try again
            self._connect_to_sheets()
            try:
                worksheet = self._get_worksheet("students")
                
                # Re-generate the student ID
                all_values = worksheet.get_all_values()
                rows = len(all_values)
                
                if rows > 0:
                    student_id = str(rows)
                else:
                    student_id = "1"
                    
                worksheet.append_row([student_id, registered_by, name, phone, subject, timestamp])
                logger.info(f"Successfully recorded student after reconnection: {name}")
            except Exception as e:
                logger.error(f"Failed to record student after reconnection: {e}")
                raise
    
    def record_payment(self, recorded_by, student_id, payment_date, amount, timestamp):
        """Record a payment for a student.
        
        Args:
            recorded_by (str): The Telegram user ID who recorded the payment
            student_id (str): The student ID
            payment_date (str): The date of the payment
            amount (str): The payment amount
            timestamp (str): The timestamp when the payment was recorded
        """
        try:
            # Get the payments worksheet
            worksheet = self._get_worksheet("payments")
            
            # Append a new row to the sheet
            worksheet.append_row([recorded_by, student_id, payment_date, amount, timestamp])
            logger.info(f"Recorded payment for student ID {student_id}: {amount}")
            
        except Exception as e:
            logger.error(f"Failed to record payment: {e}")
            # Attempt to reconnect and try again
            self._connect_to_sheets()
            try:
                worksheet = self._get_worksheet("payments")
                worksheet.append_row([recorded_by, student_id, payment_date, amount, timestamp])
                logger.info(f"Successfully recorded payment after reconnection for student ID {student_id}")
            except Exception as e:
                logger.error(f"Failed to record payment after reconnection: {e}")
                raise
    
    def get_student_report(self):
        """Get a report of all students with their attendance and payment info.
        
        Returns:
            list: A list of dictionaries with student information
        """
        try:
            # Get all worksheets
            students_worksheet = self._get_worksheet("students")
            attendance_worksheet = self._get_worksheet("attendance")
            payments_worksheet = self._get_worksheet("payments")
            
            # Get all data
            student_data = students_worksheet.get_all_records()
            attendance_data = attendance_worksheet.get_all_records()
            payment_data = payments_worksheet.get_all_records()
            
            if not student_data:
                logger.warning("No student data found for report")
                return []
                
            # Prepare report
            report = []
            
            for student in student_data:
                # Count attendance records for this student
                student_id = student.get('ID')
                if not student_id:
                    continue
                    
                attendance_count = 0
                for record in attendance_data:
                    if record.get('User ID') == student.get('Registered By'):
                        attendance_count += 1
                
                # Get latest payment
                latest_payment = None
                payment_date = "N/A"
                
                for payment in payment_data:
                    if payment.get('Student ID') == student_id:
                        latest_payment = payment.get('Amount')
                        payment_date = payment.get('Payment Date')
                
                # Create report entry
                report_entry = {
                    'id': student_id,
                    'name': student.get('Name', 'Unknown'),
                    'subject': student.get('Subject', 'Unknown'),
                    'attendance_count': attendance_count,
                    'last_payment': latest_payment or "N/A",
                    'payment_date': payment_date
                }
                
                report.append(report_entry)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate student report: {e}")
            # Attempt to reconnect and try again
            self._connect_to_sheets()
            try:
                return self.get_student_report()  # Recursive call after reconnection
            except Exception as e:
                logger.error(f"Failed to generate student report after reconnection: {e}")
                raise
