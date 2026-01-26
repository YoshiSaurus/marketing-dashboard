"""Gmail client for reading and sending emails."""

import base64
import os
import pickle
import re
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes - read and send emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """Initialize Gmail client with OAuth credentials.

        Args:
            credentials_path: Path to the Google OAuth credentials JSON file
            token_path: Path to store/read the OAuth token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail API using OAuth."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def get_unread_emails(self, subject_pattern: Optional[str] = None,
                          sender: Optional[str] = None) -> list[dict]:
        """Fetch unread emails matching the given criteria.

        Args:
            subject_pattern: Regex pattern to match email subjects
            sender: Filter by sender email address

        Returns:
            List of email dictionaries with id, subject, sender, body, and date
        """
        query = 'is:unread'
        if sender:
            query += f' from:{sender}'

        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=10
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            email_data = self._get_email_details(msg['id'])

            # Filter by subject pattern if provided
            if subject_pattern:
                if not re.search(subject_pattern, email_data['subject'], re.IGNORECASE):
                    continue

            emails.append(email_data)

        return emails

    def _get_email_details(self, message_id: str) -> dict:
        """Get full email details by message ID.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details
        """
        msg = self.service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()

        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

        # Extract body
        body = self._extract_body(msg['payload'])

        return {
            'id': message_id,
            'thread_id': msg['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'snippet': msg.get('snippet', '')
        }

    def _extract_body(self, payload: dict) -> str:
        """Extract the email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body as plain text
        """
        body = ''

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
                elif part['mimeType'] == 'multipart/alternative':
                    body = self._extract_body(part)
                    if body:
                        break

        return body

    def send_reply(self, thread_id: str, to: str, subject: str, body: str,
                   cc: Optional[str] = None) -> dict:
        """Send a reply to an email thread.

        Args:
            thread_id: Gmail thread ID to reply to
            to: Recipient email address
            subject: Email subject (will be prefixed with Re: if not already)
            body: Email body text
            cc: Optional CC recipient email address

        Returns:
            Sent message details
        """
        if not subject.lower().startswith('re:'):
            subject = f'Re: {subject}'

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent_message = self.service.users().messages().send(
            userId='me',
            body={'raw': raw, 'threadId': thread_id}
        ).execute()

        return sent_message

    def mark_as_read(self, message_id: str) -> None:
        """Mark an email as read.

        Args:
            message_id: Gmail message ID
        """
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
