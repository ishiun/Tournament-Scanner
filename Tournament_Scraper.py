import sched, time, sys, smtplib, datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from os.path import exists
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

##features
#Lookout for specific players
#alias for emails
#add another function for checking draws
#if registration Closed, remove from Open_Tournament.txt and add to Closed_Tournament.txt

##Bugs/Edge Cases
#NoSuchElementException - add a catch block
#"/" in touranment name ruins code
#same tournament 2 divisions?

OPEN_TOURNAMENTS = []
CLOSED_TOURNAMENTS = []
MY_EMAIL = "******"
MY_PASSWORD = "*****"
TO_EMAIL = "******"
s = sched.scheduler(time.time, time.sleep)
driver = webdriver.PhantomJS(executable_path='/Users/i-shiunkuo/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs')

def send_email(subject, msg_body):
    #Set up email message
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject

    #Add body to message
    body = msg_body
    msg.attach(MIMEText(body,'plain'))

    #Set up email server and send email
    server = smtplib.SMTP('smtp.gmail.com', '587')
    server.starttls()
    server.login(MY_EMAIL, MY_PASSWORD)
    text = msg.as_string()
    server.sendmail(MY_EMAIL, TO_EMAIL, text)
    server.quit()

def check_closed_tournaments():
    print("Checking Closed Tournaments...")
    closed_tournaments_file = open("Closed_Tournaments.txt", "r+")
    CLOSED_TOURNAMENTS = closed_tournaments_file.read().split("\n")
    CLOSED_TOURNAMENTS.remove("")

    for url in CLOSED_TOURNAMENTS:
        if (is_draw_released(url)):
            msg_body = "The Draw for the tournament " + tournament_name.replace("_", " ") + " has been released."
            send_email("Draw Released", msg_body)
            CLOSED_TOURNAMENTS.remove(url)

    #Clears Closed_Tournaments.txt file
    closed_tournaments_file.seek(0)
    closed_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Closed_Tournaments.txt
    for urls in CLOSED_TOURNAMENTS:
        closed_tournaments_file.write(urls + "\n")
    closed_tournaments_file.close()
    s.enter(1200,1, check_closed_tournaments)

def check_open_tournaments():
    print("Checking Open Tournaments...")
    open_tournaments_file = open("Open_Tournaments.txt", "r+")
    OPEN_TOURNAMENTS = open_tournaments_file.read().split("\n")
    OPEN_TOURNAMENTS.remove("")

    for url in OPEN_TOURNAMENTS:
        if (get_tournament_info(url)):
            OPEN_TOURNAMENTS.remove(url)

    #Clears Open_Tournaments.txt
    open_tournaments_file.seek(0)
    open_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Open_Tournaments.txt
    for urls in OPEN_TOURNAMENTS:
        open_tournaments_file.write(urls + "\n")

    open_tournaments_file.close()
    print("...")

    s.enter(3600,1, check_open_tournaments)

def get_tournament_info(url):

    driver.get(url)
    tournament_name = driver.find_element_by_xpath("//*[@id='aspnetForm']/div[3]/div[6]/div[2]/div[6]/h1").text.replace("/", "_").replace(" ", "_")
    if (is_signup_deadline_passed(driver)):

        #Remove URL from Open_Tournaments.txt
        if (is_draw_released(url)):
            msg_body = "The Draw for the tournament " + tournament_name.replace("_", " ") + " has been released."
            send_email("Draw Released", msg_body)

        #Move URL from Open_Tournaments.txt to Closed_Tournaments.txt
        else:
            CLOSED_TOURNAMENTS.append(url)
        return True

    else:
        print(tournament_name.replace("_", " "))
        print("   Status: Registration Open")
        print("   Checking for new applicants...")

        #3 second delay to allow for redirect
        time.sleep(5)

        #Get tournament info
        number_of_applicants = int(driver.find_element_by_xpath("//*[@id='ctl00_mainContent_ControlTabs7_pnlUpdate']/div[8]").text[15:])

        #Applicant file for tournament found
        if exists("/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/" + tournament_name + '.txt'):
            applicants_file = open(tournament_name + ".txt", 'r+')
            try:
                past_number_of_applicants = int(applicants_file.read().split()[0])
            except IndexError:
                past_number_of_applicants = -1

            #New players have registered for the tournament
            if past_number_of_applicants < number_of_applicants:
                print("   -> New applicants have registered")
                msg_body = str(number_of_applicants) + " new applicant(s) have registered for the " + tournament_name + "."
                send_email("New Applicants", msg_body)
                applicants_file.seek(0)
                applicants_file.truncate()
                applicants_file.write(str(number_of_applicants) + " Applicant(s) in the Men's 4.5 Singles Division")
            else:
                print("   -> No new applicants have registered")

        #Applicant file for tournament not found
        else:
            print("   -> New tournament followed")
            applicants_file = open(tournament_name + ".txt", 'w+')
            applicants_file.write(str(number_of_applicants) + " Applicant(s) in the Men's 4.5 Singles Division")
            print("   -> " + str(number_of_applicants) + " Applicant(s) found")
        applicants_file.close()
    return False

def is_draw_released(url):
    driver.get(url)
    tournament_name = driver.find_element_by_xpath("//*[@id='aspnetForm']/div[3]/div[6]/div[2]/div[6]/h1").text.replace("/", "_").replace(" ", "_")

    print(tournament_name.replace("_", " "))
    print("   Status: Registration Closed")
    print("   Searching for Draw...")

    try:
        draw = driver.find_element_by_id("ctl00_mainContent_liDraws")
        is_draw_released = True
    except NoSuchElementException:
        is_draw_released = False

    if (is_draw_released):
        print("   -> Draw has been released")
        #send email
    else:
        print("   -> Draw has not been released")

    return is_draw_released
def is_signup_deadline_passed(driver):
    try:
        deadline = driver.find_element_by_id("ctl00_mainContent_btnRegister")
    except NoSuchElementException:
        return True

    return False
def user_add_tournaments():
    if (!exists("/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/Tournaments.txt")):
        print("No tournaments saved.")
        while (add_tournaments == "y" or add_tournaments == "n"):
            add_tournaments = input("Add to tournament to follow? (y/n)")
        if (add_tournaments == "n"):
            print("Thank you for using Tournament Scanner")
            exit()
    if (add_tournaments == "y"):
        tournaments_list = open("Tournaments.txt", "w+")

def main():
    check_closed_tournaments()
    check_open_tournaments()

main()
print_time()
s.run()
driver.close()
