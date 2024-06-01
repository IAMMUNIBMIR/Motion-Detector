import smtplib
import mimetypes
from email.message import EmailMessage

SENDER = "munibsmotiondetector@gmail.com"
PASSWORD = "tfwpusgndjdapldu"

def send_email(image, recipient):
    Message = EmailMessage()
    Message["Subject"] = "New customer just showed up"
    Message["From"] = SENDER
    Message["To"] = recipient
    Message.set_content("Hey, we just saw a new customer")

    with open(image, "rb") as file:
        content = file.read()

    mime_type, _ = mimetypes.guess_type(image)
    main_type, sub_type = mime_type.split('/')
    Message.add_attachment(content, maintype=main_type, subtype=sub_type)

    with smtplib.SMTP("smtp.gmail.com", 587) as gmail:
        gmail.ehlo()
        gmail.starttls()
        gmail.login(SENDER, PASSWORD)
        gmail.send_message(Message)
