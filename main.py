#!/Users/liamwebsterreal/Documents/projects/bills_script/venv/bin/python

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import yaml
import smtplib
import ssl
import json

# Login Function
def login(driver, url, usernameId, username, passwordId, password, submit_buttonId):
    driver.get(url)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, submit_buttonId))
    )   #wait for page to load, so element with ID 'username' is visible
    driver.find_element(By.XPATH,usernameId).send_keys(username)
    driver.find_element(By.XPATH, passwordId).send_keys(password)
    driver.find_element(By.XPATH, submit_buttonId).click()

def main():

###################################### 
#               Setup                # 
###################################### 

    # Loading Login Info from yaml file
    with open('C:/Users/liamc/Documents/projects/bills_script/LoginInfo.yml', 'r') as file:
        conf = yaml.safe_load(file)
    BT_user = conf['BandT']['user']
    BT_password = conf['BandT']['password']
    pge_user = conf['pge']['user']
    pge_password = conf['pge']['password']
    sonic_user = conf['sonic']['user']
    sonic_password = conf['sonic']['password']

    # Setting selenium up
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu') 
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Initializing Error dictionary
    Error=False
    Errors={
        "B&T": None,
        "PG&E": None,
        "Sonic": None,
    }

    # Initializing Balances to zero
    total_util = 0
    pge_bal = 0
    BT_bal = 0
    sonic_bal = 0


###################################### 
#      Scraping and Extracting       # 
###################################### 

    #PG&E 
    try:
        login(driver, "https://www.pge.com/", """//*[@id="username"]""", "liamcw2001@gmail.com", """//*[@id="password"]""", "magicStuff404", """//*[@id="home_login_submit"]""")
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "spntotalAmountDueUI"))
        )   #wait for page to load, so element with ID 'username' is visible
        soup = BeautifulSoup(driver.page_source, "html.parser")
        balance = soup.find(id="spntotalAmountDueUI")
        pge_bal = balance.text
        pge_bal = pge_bal.replace(' ', '').replace('\n', '').replace('$', '')
        pge_bal = float(pge_bal)
    except:
        print("no good")
        Error = True
        Errors["PG&E"] = "Error while extracting bill information from https://m.pge.com/"

    #Brick and Timber
    try:
        login(driver,"https://properties-rentbt.securecafe.com/residentservices/apartmentsforrent/userlogin.aspx", """//*[@id="Username"]""", BT_user, """//*[@id="Password"]""", BT_password, """//*[@id="SignIn"]""")
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "MyAccountBalanceView"))
        )   #wait for page to load, so element with ID 'username' is visible
        soup = BeautifulSoup(driver.page_source, "html.parser")
        balance = soup.find("div", class_="span6 total-balance text-error")
        BT_bal = balance.text
        BT_bal = BT_bal.strip('$').replace(',', '').strip(' ').strip('\n')
        BT_bal = float(BT_bal)
        BT_util = BT_bal - 6595.00
    except:
        Error = True
        Errors["B&T"] = "Error while extracting bill information from https://properties-rentbt.securecafe.com"
        
    #Sonic
    try: 
        login(driver, "https://members.sonic.net/", """//*[@id="user"]""", sonic_user, """//*[@id="pw"]""", sonic_password, """//*[@id="login"]/input[2]""")
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "col-md-12"))
        )   #wait for page to load, so element with ID 'username' is visible
        driver.find_element(By.XPATH, """//*[@id="main"]/div/table/tbody/tr/td[2]/div/div[3]/table/tbody/tr/td/table/tbody/tr/td/div/div/div[3]/div/div[2]/div/a[1]""").click()
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, """//*[@id="main"]/div/table/tbody/tr/td[2]/div/div[3]/table/tbody/tr/td/table/tbody/tr/td/div[1]/div[1]/div/div/table/tbody/tr[5]/td[2]/span"""))
        )   #wait for page to load, so element with ID 'username' is visible
        soup = BeautifulSoup(driver.page_source, "html.parser")
        balance = soup.find(class_="noborder amount")
        sonic_bal = balance.text
        sonic_bal = sonic_bal.strip(' ').strip('\n').strip('$')
        sonic_bal = float(sonic_bal)
    except:
        Error = True
        Errors["Sonic"] = "Error while extracting bill information from https://members.sonic.net/"

    # Handling Util Split logic
    total_util = BT_util + pge_bal + sonic_bal
    individual_util = total_util / 3
    individual_util = round(individual_util + 0.005, 2)
    total_bill = 6595 + total_util
    Liam_total = 2000 + individual_util
    Noah_total = 2200 + individual_util
    Josh_total = 2395 + individual_util


###################################### 
#             Emailing               # 
###################################### 

    # Liam Email
    ctx = ssl.create_default_context()
    password = "zbqwelcdfdbvqssq"    # Your app password goes here
    sender = "liam.webster.dev@gmail.com"    # Your e-mail address
    receiver = "liamcw2001@gmail.com" # Recipient's address
    subject = "APT 403 Monthly Bill"
    if(Error):
        text = json.dumps(Errors)
    else:
        text = """
    -------------------------------------------
    Hello Liam,

    Monthly APT 403 Cost Breakdown:
        B&T Utils: $%f
        PGE Utils: $%f
        Sonic Utils: $%f
    Total Utilities: $%f
    Total Due: $%f

    Individual Utilities: $%f
    Rent Rate: $%f
    Liam you are due to pay: $%f
    -------------------------------------------
    """ % (BT_util, pge_bal, sonic_bal, total_util, total_bill, individual_util, 2000.00, Liam_total)
    message = 'Subject: {}\n\n{}'.format(subject, text)
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message)

    # Noah Email
    ctx = ssl.create_default_context()
    password = "zbqwelcdfdbvqssq"    # Your app password goes here
    sender = "liam.webster.dev@gmail.com"    # Your e-mail address
    receiver = "ngetz24@berkeley.edu" # Recipient's address
    subject = "APT 403 Monthly Bill"
    if(Error):
        exit()
    else:
        text = """
    -------------------------------------------
    Hello Noah,

    Monthly APT 403 Cost Breakdown:
        B&T Utils: $%f
        PGE Utils: $%f
        Sonic Utils: $%f
    Total Utilities: $%f
    Total Due: $%f

    Individual Utilities: $%f
    Rent Rate: $%f
    Noah you are due to pay: $%f
    -------------------------------------------
    """ % (BT_util, pge_bal, sonic_bal, total_util, total_bill, individual_util, 2200.00, Noah_total)
    message = 'Subject: {}\n\n{}'.format(subject, text)
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message)

    # Josh Email
    ctx = ssl.create_default_context()
    password = "zbqwelcdfdbvqssq"    # Your app password goes here
    sender = "liam.webster.dev@gmail.com"    # Your e-mail address
    receiver = "ophir.josh@gmail.com" # Recipient's address
    subject = "APT 403 Monthly Bill"
    if(Error):
        exit()
    else:
        text = """
    -------------------------------------------
    Hello Josh,

    Monthly APT 403 Cost Breakdown:
        B&T Utils: $%f
        PGE Utils: $%f
        Sonic Utils: $%f
    Total Utilities: $%f
    Total Due: $%f

    Individual Utilities: $%f
    Rent Rate: $%f
    Josh you are due to pay: $%f
    -------------------------------------------
    """ % (BT_util, pge_bal, sonic_bal, total_util, total_bill, individual_util, 2395.00, Josh_total)
    message = 'Subject: {}\n\n{}'.format(subject, text)
    with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, message)


    
    
if __name__ == "__main__":
    main()