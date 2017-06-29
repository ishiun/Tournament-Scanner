import sched, time, sys, smtplib, datetime, os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import Select
from os.path import exists
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MY_EMAIL = "******"
MY_PASSWORD = "******"
TO_EMAIL = "******"

#Sets up scheduler
s = sched.scheduler(time.time, time.sleep)

#Sets up browser
driver = webdriver.PhantomJS(executable_path='/Users/i-shiunkuo/Side_Projects/Tournament_Scanner/phantomjs-2.1.1-macosx/bin/phantomjs')

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
    print("Checking Closed Tournaments... \n----------------")
    closed_tournaments_file = open("Tournaments/Closed_Tournaments.txt", "r+")
    closed_tournaments = closed_tournaments_file.read().split("\n")
    closed_tournaments.remove("")

    for url in closed_tournaments:

        driver.get(url)
        time.sleep(3)

        #Gets tournament info
        tournament_name = driver.find_element_by_class_name("tournament_search").text.replace("/", "_").replace(" ", "_")
        tournament_name_clean = tournament_name.replace("_", " ")
        try:
            division = Select(driver.find_element_by_class_name("TournamentHome_SpecialCSS_TopAnchor")).first_selected_option.text.split(" ")[-1]
        except NoSuchElementException:

            url += "#&&s=1"
            driver.get(url)
            time.sleep(3)
            division = "Events"
        print(tournament_name_clean)
        print("   Status: Registration Closed")
        if (division == "Events"):
            print("   Searching for Draws...")
        else:
            print("   Searching for " + division + " Draw...")

        if (is_draw_released(division)):
            if (division == "Events"):
                print("   -> Draws have been released\n")
                msg_body = "The Draws for the tournament " + tournament_name_clean + " has been released.\n\n" + url
                send_email("Draw released", msg_body)
            else:
                print("   -> " + division + " Draw has been released\n")
                msg_body = "The " + division + " Draw for the tournament " + tournament_name_clean + " has been released.\n\n" + url
                send_email(division + " Draw Released", msg_body)
            closed_tournaments.remove(url)
        else:
            if (division == "Events"):
                print("   -> Draws has not been released\n")
            else:
                print("   -> " + division + " Draw has not been released\n")

    #Clears Closed_Tournaments.txt file
    closed_tournaments_file.seek(0)
    closed_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Closed_Tournaments.txt
    for urls in closed_tournaments:
        closed_tournaments_file.write(urls + "\n")

    closed_tournaments_file.close()
    s.enter(60,1, check_closed_tournaments)
    are_tournament_files_empty()
    print_time()

def check_open_tournaments():
    print("Checking Open Tournaments... \n----------------")
    open_tournaments_file = open("Tournaments/Open_Tournaments.txt", "r+")
    open_tournaments = open_tournaments_file.read().split("\n")
    open_tournaments.remove("")

    for url in open_tournaments:
        if (is_tournament_closed(url)):
            #Remove URL from Open_Tournaments.txt
            open_tournaments.remove(url)

    #Clears Open_Tournaments.txt
    open_tournaments_file.seek(0)
    open_tournaments_file.truncate()

    #Writes tournament links for draws that have not been released into Open_Tournaments.txt
    for urls in open_tournaments:
        open_tournaments_file.write(urls + "\n")

    open_tournaments_file.close()
    are_tournament_files_empty()
    print_time()
    s.enter(300,1, check_open_tournaments)

def is_tournament_closed(url):
    try:
        driver.get(url)
    except WebDriverException:
        return True;

    #3 second delay to allow for redirect
    time.sleep(3)

    tournament_name = driver.find_element_by_class_name("tournament_search").text.replace("/", "_").replace(" ", "_")
    tournament_name_clean = tournament_name.replace("_", " ")
    try:
        division = Select(driver.find_element_by_class_name("TournamentHome_SpecialCSS_TopAnchor")).first_selected_option.text.split(" ")[-1]

    except NoSuchElementException:
        #Changes URL to direct to applicants and retries the driver
        url += "#&&s=1"
        driver.get(url)
        time.sleep(5)
        division = "Events"

    print(tournament_name_clean)

    if (is_signup_deadline_passed(driver)):
        print("   Status: Registration Closed")

        #If draw has been released, send notification email
        if (is_draw_released(division)):
            if (division == "Events"):
                print("   The Draws have been released.\n")
                msg_body = "The Draws for the tournament " + tournament_name_clean + " have been released.\n\n" + url
                send_email("Draws released", msg_body)
            else:
                print("The " + division + " Draw has been released.\n")
                msg_body = "The " + division + " Draw for the tournament " + tournament_name_clean + " has been released.\n\n" + url
                send_email(division + "Draw Released", msg_body)

        #Appends URL to Closed_Tournaments.txt
        else:
            if (division == "Events"):
                print("   -> Draws have not been released")
            else:
                print("   -> " + division + " Draw has not been released")
            print("   -> Moving tournaments to Closed Tournaments list...\n")
            Closed_Tournaments_file = open("Tournaments/Closed_Tournaments.txt", "a")
            Closed_Tournaments_file.write("\n" + url)
        return True

    #If registration is still open, checks for new applicants
    else:
        check_for_new_applicants(tournament_name, tournament_name_clean, division, url)
        return False

def check_for_new_applicants(tournament_name, tournament_name_clean, division, url):
        print("   Status: Registration Open")
        if (division == "Events"):
            print("   Checking for new applicants...")
        else:
            print("   Checking for new " + division + " applicants...")

        #Get tournament info
        number_of_applicants = int(driver.find_element_by_class_name("total").text[15:])
        file_name = division + "_" + tournament_name + ".txt"

        #Applicant file for tournament found
        if exists("Tournament_Info/" + file_name):
            applicants_file = open("Tournament_Info/" + file_name, 'r+')
            try:
                past_number_of_applicants = int(applicants_file.read().split()[0])
            except IndexError:
                past_number_of_applicants = 0

            #New players have registered for the tournament
            if past_number_of_applicants < number_of_applicants:
                number_of_new_applicants = str(number_of_applicants - past_number_of_applicants)
                if (division == "Events"):
                    print("   -> " + number_of_new_applicants + " new applicant(s) have registered\n")
                    msg_body = number_of_new_applicants + " new applicant(s) have registered for the " + tournament_name_clean + ".\n\n" + url
                    send_email("New Applicants Registered", msg_body)
                else:
                    print("   -> " + number_of_new_applicants+ " new " + division + " applicant(s) have registered\n")
                    msg_body = number_of_new_applicants + " new " + division + " applicant(s) have registered for the " + tournament_name_clean + ".\n\n" + url
                    send_email("New " + division + " Applicants Registered", msg_body)

                #Updates touranment information text files
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
            applicants_file = open("Tournament_Info/" + file_name, 'w+')

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

    return is_draw_released

def is_signup_deadline_passed(driver):
    try:
        deadline = driver.find_element_by_id("ctl00_mainContent_btnRegister")
    except NoSuchElementException:
        return True
    return False

def print_time():
    print(time.strftime('%I:%M %p') + '\n...')

def are_tournament_files_empty():
        if ((os.stat("Tournaments/Open_Tournaments.txt").st_size < 1) and (os.stat("Tournaments/Closed_Tournaments.txt").st_size < 1)):
            print("No more tournaments being followed")
            exit()

def create_tournaments_files():
    if (not exists("Tournaments/Open_Tournaments.txt")):
        open("Tournaments/Open_Tournaments.txt", "w+").close()
    if (not exists("Tournaments/Closed_Tournaments.txt")):
        open("Tournaments/Closed_Tournaments.txt", "w+").close()

def main():
    create_tournaments_files()
    check_closed_tournaments()
    check_open_tournaments()

main()
s.run()
driver.close()
