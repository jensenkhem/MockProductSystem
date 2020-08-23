import sqlite3
import datetime
import random
import string
from setup import *
from saleInfo import *

def postSale(cursor, connection, email): #check the types of everything and HOW TO ENTER TIME INTO DATATBASE
    
    inputPid = input("Enter product id: ")
    if (inputPid==""):
        inputPid = None 
    inputEndDate = input("Enter sale end date(YYYY-MM-DD): ")        
    inputEndTime = input("Enter sale end time(HH:MM:SS):")
    inputDescr = input("Enter sale description: ")
    inputCond = input("Enter sale condition: ")
    inputRprice = input("Enter reserve price: ")

    cursor.execute(''' SELECT sid FROM sales; ''') # gets all sid from sales
    allSaleId = cursor.fetchall()
    inputSid = getNewId(allSaleId, cursor, connection) # passes all the sids to function to get unique id

    if (inputPid != None and checkSalePid(inputPid, cursor, connection) == False): #checks if pid exists if pid is not an empty string
        print("Pid does not exist")
        return

    currentDayInfo = datetime.datetime.now() # gets current year,day,month, and time
    splitDate = inputEndDate.split("-") # splits input day to get year,month, and day
    todayDate = datetime.date(currentDayInfo.year, currentDayInfo.month, currentDayInfo.day) # formats today's values from datetime function into python date format

    try: # check to see if input date is valid format
        enteredDate = datetime.date(int(splitDate[0]),int(splitDate[1]),int(splitDate[2])) # formats inputed values into python date format
    except:
        print("Incorrect date formatting")
        return
    
    if (enteredDate <= todayDate): # compared today's date with entered date
        if (inputEndTime < currentDayInfo.strftime("%H:%M")): # checks if there is still time left today
            print("End time and date needs to be in the future")
            return
        else:
            print("Day entered is in the past")
            return
    try:   
       inputHourMin = inputEndTime.split(":") # splits inputed time into an array
       if (inputHourMin[0] > "24" or inputHourMin[1] > "59"): # checks to see if values are reasonable
           print("Incorrect format of time")
           return
    except:
        print("Invalid time format!")
        return
    try:
        float(inputRprice)
    except:
        print("Reserve price has to be a price")
        return
    
    inputEndDate = inputEndDate +" "+ inputEndTime # adds date and time to be proper format for sql table
    cursor.execute(''' INSERT INTO sales(sid,lister,pid,edate,descr,cond,rprice) VALUES(?,?,?,?,?,?,?);''', (inputSid, email, inputPid, inputEndDate, inputDescr, inputCond, inputRprice)) #enter sales into data base
    connection.commit()
    print("Sale successfuly posted!")
    return

def checkSalePid(inputPid, cursor, connection):
    # checks to see if user enters a valid product id
    # returns true if product pid is valid
    # returns false if product pid does not exist
    
    cursor.execute('''SELECT pid FROM products;''')
    allPid = cursor.fetchall() # gets all the pids from products

    for each in allPid:
        if (inputPid == each[0]): # if inputed pid exists in product pid table, return true
            return True
    return False

def findUsers(cursor, connection, email):
    keyword = input("Enter keyword: ")
    query = '''SELECT users.email, users.name, users.city FROM users WHERE users.email LIKE '%'''+keyword+'''%' or users.name LIKE '%'''+keyword+'''%' ''' #searches for keyword in the query 
    cursor.execute(query)
    result = cursor.fetchall() # gets all user information in a tuple
    if (result == []): # checks if no matching results
        print("No users match that keyword")
        return
    else:
        print("Users found :")
        for r in result:
            print(r)


    selectedUser = input("Select a user: ")

    inResult = False
    for eachPerson in result:
        if (selectedUser == eachPerson[0]):
            inResult = True
    if (inResult == False):
        print("User selected not in results. Please type valid email.")
        return
    
    action = input("Choose 'wr' to write a review, 'l' to list active listings, 'ar' to list all reviews of the user: ")
    if (action == "wr"):
        writeReview(selectedUser, email, cursor, connection)
    elif (action == "l"):
        list_active_sales_user(selectedUser, cursor, connection)
    elif (action == "ar"):
        get_reviews_user(selectedUser, cursor, connection)
    else:
        print("Invalid option")

    connection.commit()
    return

def writeReview(reviewee, email, cursor, connection):
    # adds review written by user into review table

   # checks if the user already wrote a review on selected user
    cursor.execute('''SELECT reviewer FROM reviews WHERE reviewee = ? ''', (reviewee,))
    results = cursor.fetchall()
    for reviewer in results:
        if (reviewer[0] == email):
            print("User cannot write more than one review on user")
            return

    userRText = input("Write a review: ")
    userRating = int(input("Write a rating(between 1 and 5 inclusive): "))
    if (userRating >= 1 and userRating <= 5):#only add reviews where rating between 1 and 5
        cursor.execute('''INSERT INTO reviews VALUES(?,?,?,?,datetime('now'));''',(email, reviewee, userRating, userRText)) # insert into review table
    else:
        print("Invalid rating")
    connection.commit()
    return

def get_reviews_user(lister, cursor, connection):
    # Query the data to get all of the reviews of a given user!
    cursor.execute('''SELECT reviewer, rating, rtext, rdate FROM reviews WHERE reviewee LIKE ? ''', (lister,))
    results = cursor.fetchall()
    print('\n')
    for result in results:
        print(result)
    connection.commit()

def list_active_sales_user(lister, cursor, connection):
    # Query the data to list all the active sales of the given user!
    cursor.execute('''SELECT s.descr, s.sid, s.rprice, strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60 
FROM sales s
WHERE s.sid not in (select  s.sid 
		from sales s, bids b
		where s.sid = b.sid)
and edate > date('now') and s.lister LIKE ?
UNION 
Select s.descr, s.sid, max(b.amount), strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60
from sales s, bids b 
where s.sid = b.sid and edate > date('now') and s.lister LIKE ?
group by s.descr, s.sid ORDER by strftime('%s',s.edate) / 60 - strftime('%s','now') / 60 ;''', (lister, lister))
    results = cursor.fetchall()
    print('\n')
    for result in results:
        print(result)
    connection.commit()


def getNewId(idList, cursor, connection):
    # NOTE BEFORE CALLING THIS FUNCTION TYPE:
    #cursor.execute(''' SELECT sid FROM sales; ''')
    #allIds = cursor.fetchall()
    #getNewId(allIds)
    # returns new, unique id which is not already in the specified table 
    isNotUnique = True
    isMatching = False
    random.seed()
    while (isNotUnique == True):
        randomLetter = random.choice(string.ascii_letters)
        randomLetter = randomLetter.upper()
        randomNum = str(random.randint(0,500))
        newId = randomLetter+randomNum
        for eachId in idList:
            if (eachId[0] == newId):
                isMatching = True
        isNotUnique = isMatching
        isMatching = False
    return newId


'''    
def main():
    global connection,cursor
    connection = sqlite3.connect('./test.db')
    cursor = connection.cursor()
    postSale()
    #findUsers()
   # allActiveSales()
    #moreInfo()
    connection.commit()
    connection.close()
    return

main()
'''
