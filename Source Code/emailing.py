import smtplib
import mimetypes
from email.message import EmailMessage

SENDER = "munibsmotiondetector@gmail.com"
PASSWORD = "tfwpusgndjdapldu"

def send_email(image_path, recipient_email):
    if not SENDER or not PASSWORD:
        print("Error: Sender email or password not provided.")
        return

    message = EmailMessage()
    message["Subject"] = "New customer just showed up"
    message.set_content("Hey, we just saw a new customer")

    with open(image_path, "rb") as file:
        content = file.read()

    mime_type, _ = mimetypes.guess_type(image_path)
    main_type, sub_type = mime_type.split('/')
    message.add_attachment(content, maintype=main_type, subtype=sub_type)

    message["To"] = recipient_email

    with smtplib.SMTP("smtp.gmail.com", 587) as gmail:
        gmail.ehlo()
        gmail.starttls()
        gmail.login(SENDER, PASSWORD)
        gmail.send_message(message)
