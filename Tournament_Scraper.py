import sched, time, sys, smtplib, datetime, os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from os.path import exists
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#added since last push
#scraped division from usta site
#added division and link to tournament in emails

##features
#directory with touranment files
#division tournament file names
#add var for replace.("","")
#2 funcs sending applicants/draw email
#sends a warning email when deadline comes close
#Lookout for specific players

##Bugs/Edge Cases
#breaks when players tab is removed
#remove global variable lists
#change xpaths to ids or class names
#exit program if no tournaments in either files
#if Open_Tournaments.txt or Closed_Tournaments.txt doesnt exist
#NoSuchElementException - add a catch block
#same tournament 2 divisions?

OPEN_TOURNAMENTS = []
CLOSED_TOURNAMENTS = []
MY_EMAIL = "***"
MY_PASSWORD = "***"
TO_EMAIL = "****"

s = sched.scheduler(time.time, time.sleep)
driver = webdriver.PhantomJS(executable_path='/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/PhantomJs/phantomjs-2.1.1-macosx/bin/phantomjs')

def send_email(subject, msg_body):
    #Set up email message
    msg = MIMEMultipart()
    msg['From'] = "Tournament Scanner"
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
    are_tournament_files_empty()
    print("Checking Closed Tournaments... \n----------------")
    closed_tournaments_file = open("Closed_Tournaments.txt", "r+")
    CLOSED_TOURNAMENTS = closed_tournaments_file.read().split("\n")
    CLOSED_TOURNAMENTS.remove("")

    for url in CLOSED_TOURNAMENTS:
        driver.get(url)
        time.sleep(3)

        tournament_name = driver.find_element_by_class_name("tournament_search").text.replace("/", "_").replace(" ", "_")
        division = Select(driver.find_element_by_class_name("TournamentHome_SpecialCSS_TopAnchor")).first_selected_option.text.split(" ")[-1]

        print(tournament_name.replace("_", " "))
        print("   Status: Registration Closed")
        if (division == "Events"):
            print("   Searching for Draws...")
        else:
            print("   Searching for " + division + " Draw...")

        if (is_draw_released(division)):
            if (division == "Events"):
                msg_body = "The Draws for the tournament " + tournament_name.replace("_", " ") + " has been released.\n\n" + url
                send_email("Draw released", msg_body)
            else:
                msg_body = "The " + division + " Draw for the tournament " + tournament_name.replace("_", " ") + " has been released.\n\n" + url
                send_email(division + " Draw Released", msg_body)
            CLOSED_TOURNAMENTS.remove(url)

    #Clears Closed_Tournaments.txt file
    closed_tournaments_file.seek(0)
    closed_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Closed_Tournaments.txt
    for urls in CLOSED_TOURNAMENTS:
        closed_tournaments_file.write(urls + "\n")
    closed_tournaments_file.close()
    s.enter(1200,1, check_closed_tournaments)
    print_time()

def check_open_tournaments():
    are_tournament_files_empty
    print("Checking Open Tournaments... \n----------------")
    open_tournaments_file = open("Open_Tournaments.txt", "r+")
    OPEN_TOURNAMENTS = open_tournaments_file.read().split("\n")
    OPEN_TOURNAMENTS.remove("")

    for url in OPEN_TOURNAMENTS:
        if (is_tournament_closed(url)):
            #Remove URL from Open_Tournaments.txt
            OPEN_TOURNAMENTS.remove(url)

    #Clears Open_Tournaments.txt
    open_tournaments_file.seek(0)
    open_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Open_Tournaments.txt
    for urls in OPEN_TOURNAMENTS:
        open_tournaments_file.write(urls + "\n")

    open_tournaments_file.close()
    print_time()

    s.enter(3600,1, check_open_tournaments)

def is_tournament_closed(url):

    driver.get(url)

    #3 second delay to allow for redirect
    time.sleep(3)

    tournament_name = driver.find_element_by_class_name("tournament_search").text.replace("/", "_").replace(" ", "_")
    division = Select(driver.find_element_by_class_name("TournamentHome_SpecialCSS_TopAnchor")).first_selected_option.text.split(" ")[-1]

    if (is_signup_deadline_passed(driver)):

        if (is_draw_released(url)):
            if (division == "Events"):
                msg_body = "The Draws for the tournament " + tournament_name.replace("_", " ") + " have been released.\n\n" + url
                send_email("Draws released", msg_body)
            else:
                msg_body = "The " + division + " Draw for the tournament " + tournament_name.replace("_", " ") + " has been released.\n\n" + url
                send_email(division + "Draw Released", msg_body)

        #Appends URL to Closed_Tournaments.txt
        else:
            Closed_Tournaments_file = open("Closed_Tournaments.txt", "a")
            Closed_Tournaments_file.write("\n" + url)
        return True

    else:
        check_for_new_applicants(tournament_name, division)
        return False

def check_for_new_applicants(tournament_name, division):
        print(tournament_name.replace("_", " "))
        print("   Status: Registration Open")
        if (division == "Events"):
            print("   Checking for new applicants...")
        else:
            print("   Checking for new " + division + " applicants...")

        #Get tournament info
        try:
            number_of_applicants = int(driver.find_element_by_xpath("//*[@id='ctl00_mainContent_ControlTabs7_pnlUpdate']/div[8]").text[15:])
        except NoSuchElementException:
            time.sleep(5)
            number_of_applicants = int(driver.find_element_by_xpath("//*[@id='ctl00_mainContent_ControlTabs7_pnlUpdate']/div[8]").text[15:])
        #move to is_tournament_closed


        #Applicant file for tournament found
        if exists("/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/" + tournament_name + '.txt'):
            applicants_file = open(tournament_name + ".txt", 'r+')
            try:
                past_number_of_applicants = int(applicants_file.read().split()[0])
            except IndexError:
                past_number_of_applicants = 0

            #New players have registered for the tournament
            if past_number_of_applicants < number_of_applicants:
                number_of_new_applicants = str(number_of_applicants - past_number_of_applicants)
                if (division == "Events"):
                    print("   -> " + number_of_new_applicants + " new applicant(s) have registered\n")
                    msg_body = number_of_new_applicants + " new applicant(s) have registered for the " + tournament_name.replace("_", " ") + "."
                    send_email("New Applicants Registered", msg_body)
                else:
                    print("   -> " + number_of_new_applicants+ " new " + division + " applicant(s) have registered\n")
                    msg_body = number_of_new_applicants + " new " + division + " applicant(s) have registered for the " + tournament_name.replace("_", " ") + "."
                    send_email("New " + division + " Applicants Registered", msg_body)
                applicants_file.seek(0)
                applicants_file.truncate()
                applicants_file.write(str(number_of_applicants) + " Applicant(s) in the " + division + " Division")
            else:
                if (division == "Events"):
                    print("   -> No new applicants have registered\n")
                else:
                    print("   -> No new " + division + " applicants have registered\n")

        #Applicant file for tournament not found
        else:
            print("   -> New tournament followed")
            applicants_file = open(tournament_name + ".txt", 'w+')

            applicants_file.write(str(number_of_applicants) + " Applicant(s) in the " + division + " Division")
            if (division == "Events"):
                print("   -> " + str(number_of_applicants) + " Applicant(s) found\n")
            else:
                print("   -> " + str(number_of_applicants) + " " + division +  " Applicant(s) found\n")
        applicants_file.close()

def is_draw_released(division):

    try:
        draw = driver.find_element_by_id("ctl00_mainContent_liDraws")
        is_draw_released = True
    except NoSuchElementException:
        is_draw_released = False

    if (is_draw_released):
        if (division == "Events"):
            print("   -> Draws have been released")
        else:
            print("   ->" + division + " Draw has been released")
    else:
        if (division == "Events"):
            print("   -> Draws have not been released")
        else:
            print("   ->" + division + " Draw has not been released")

    return is_draw_released

def is_signup_deadline_passed(driver):
    try:
        deadline = driver.find_element_by_id("ctl00_mainContent_btnRegister")
    except NoSuchElementException:
        return True
    return False

def print_time():
    time = datetime.datetime.now()
    day = "AM"
    hour = time.hour
    if (hour > 11):
        day = "PM"
    if (hour > 12):
        hour -= 12
    if (hour == 0):
        hour = 12;
    print("...")
    print(str(hour) + ":" + str(time.minute) + " " + day)
    print("...")
def are_tournament_files_empty():
#    try:
#    os.path.getsize("C:/Tournaments/Open_Tournaments.txt")
    '''        if ((os.stat("Open_Tournament.txt").st_size < 1) and (os.stat("Closed_Tournaments.txt").st_size < 1)):
            print("No tournaments being followed")
            exit()
    except FileNotFoundError:
    '''

def main():
    check_closed_tournaments()
    check_open_tournaments()

main()
s.run()
driver.close()
