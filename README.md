# Tournament-Scanner
Sends user an email notifying the user when a new player has signed up for a specific division in a USTA tournament, and when the draw has been released.

# Usage
- Download PhantomJs
- Add executable_path for your PhantomJs when setting up the driver

1. Find the USTA Tennis Tournament page you would like to follow
2. Scroll through the divisions on the page and choose any division
3. Add link to the TOURNAMENTS list
4. Set up email
  - MY_EMAIL = email to send notification from
  - MY_PASSWORD = password to MY_EMAIL
  - TO_EMAIL = recipient of notifications

**** Have to change SMTP server settings/port number if you're not using gmail account to send emails.
     iCloud: smtp.mail.me.com, 587
     Yahoo: plus.smtp.mail.yahoo.com, 465
    
Run Using:  
python3 Tournament_Scanner.py 
