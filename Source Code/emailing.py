import smtplib
import mimetypes
from email.message import EmailMessage

SENDER = "munibsmotiondetector@gmail.com"
PASSWORD = "tfwpusgndjdapldu"
RECIPIENT = "munibmir09@gmail.com"  # Replace with the actual recipient email address

def Alert(Image):
    Message = EmailMessage()
    Message["Subject"] = "New customer just showed up"
    Message.set_content("Hey, we just saw a new customer")

    with open(Image, "rb") as file:
        content = file.read()

    mime_type, _ = mimetypes.guess_type(Image)
    main_type, sub_type = mime_type.split('/')
    Message.add_attachment(content, maintype=main_type, subtype=sub_type)

    with smtplib.SMTP("smtp.gmail.com", 587) as gmail:
        gmail.ehlo()
        gmail.starttls()
        gmail.login(SENDER, PASSWORD)
        gmail.send_message(Message)
