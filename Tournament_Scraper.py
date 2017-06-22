import sched, time, sys, smtplib
from selenium import webdriver
from os.path import exists
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Lookout for specific players
#applicants in file could be double digits, read until hit a space
#alias for emails

TOURNAMENTS = ["http://tennislink.usta.com/Tournaments/TournamentHome/Tournament.aspx?T=202303#&&s=1A8"]
MY_EMAIL = "******"
MY_PASSWORD = "******"
TO_EMAIL = "********"

s = sched.scheduler(time.time, time.sleep)

def send_email(tournament_name):
    #Set up email message
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = tournament_name

    #Add body to message
    body = "There are new applicants for " + tournament_name + "."
    msg.attach(MIMEText(body,'plain'))

    #Set up email server and send email
    server = smtplib.SMTP('smtp.gmail.com', '587')
    server.starttls()
    server.login(MY_EMAIL, MY_PASSWORD)
    text = msg.as_string()
    server.sendmail(MY_EMAIL, to_email, text)
    server.quit()


def get_tournament_info(url):
    driver = webdriver.PhantomJS(executable_path='/Users/i-shiunkuo/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs')
    driver.get(url)

    #1 second delay to allow for redirect
    time.sleep(1)

    #Get tournament info
    tournament_name = driver.find_element_by_xpath("//*[@id='aspnetForm']/div[3]/div[6]/div[2]/div[6]/h1").text
    number_of_4_5_applicants = driver.find_element_by_xpath("//*[@id='ctl00_mainContent_ControlTabs7_pnlUpdate']/div[8]").text[15:]

    if exists("/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/" + str(tournament_name) + '.txt'):
        applicants_file = open(str(tournament_name) + ".txt", 'r+')

        #New players have registered for the tournament
        if int(applicants_file.read(1)) < int(number_of_4_5_applicants):
            send_email(tournament_name)
            applicants_file.truncate()
            applicants_file.write(number_of_4_5_applicants + " Applicants in the Men's 4.5 Singles Division")

    #File not found
    else:
        applicants_file = open(str(tournament_name) + ".txt", 'w+')
        applicants_file.write(number_of_4_5_applicants + " Applicants in the Men's 4.5 Singles Division")

    applicants_file.close()
    driver.close()

def main():
    for url in TOURNAMENTS:
        get_tournament_info(url)
    s.enter(600,1, main)

main()
s.run()
