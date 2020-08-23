import sqlite3
import time
import getpass
import sys
from saleUser import *
from saleInfo import *
from productBid import *

# Initialize program variables
connection = None
cursor = None

def connect(path):
    # Basic function to set up the cursor and connection to the database
    global connection, cursor
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()
    return

def main():
    # Program workflow
    global connection, cursor
    path="./" + sys.argv[1] # Name of the database
    connect(path)
    current_user = None
   # Login stuff
    while(current_user == None):
        current_user = change_user()
        if(current_user == False):
            return
    # Main program loop!
    while(True):
        choice = input("Would you like to list products (1), Search for sales (2), Post a sale (3), or Search for users (4) -> Press 'q' to quit, or 'l' to logout: ")
        if(choice == '1'):
            list_product(cursor, connection, current_user)
        elif(choice == '2'):
            results = search_for_sales()
            choice2 = input('Would you like to select a specific sale? (y/n)')
            if choice2 == 'y':
                success = moreInfo(results, current_user, cursor, connection) 
            else:
                continue
        elif(choice == '3'):
            postSale(cursor, connection, current_user)
        elif(choice == '4'):
            findUsers(cursor, connection, current_user)
        elif(choice == 'q'):
            return
        elif(choice == 'l'):
            while(True):
                current_user = change_user()
                if(current_user == None):
                    continue
                if(current_user == False):
                    return
                else:
                    break
        else:
            continue
        
    return

def logout(user):
    user = None
    return user
    

def change_user():
    # Function to give the user the ability to login to an account/register
    while(True):
       resp =  input("Type 'r' to register, 'l' to login, or 'q' to quit: ")
       # Register
       if resp == 'r':
           new_email = input("Please enter a valid email address: ")
           # new_pwd = input("Please enter your password: ")
           new_pwd = getpass.getpass("Please enter your password: ")
           if(register(new_email, new_pwd)):
               print("Successfully registered")
               return new_email
           else:
               print("Registration not successful")
               return None
       # Register
       elif resp == 'l':
           return login()
       elif resp == 'q':
           return False
    return 
      
def register(email, pwd):
    global connection, cursor
    # Here we insert this new data into the users table in the database
    # Make sure to protect against injections here
    # Returns True upon successful registration, False otherwise
    user_name = input("Input your name: ")
    user_city = input("Input your city: ")
    user_gender = input("Input your gender (M/F): ")
    if(user_gender not in ('M','F')):
        print("Invalid entry")
        return False
    insertions = (email, user_name, pwd, user_city, user_gender)
    try:
        # Insert the inputted data into the db
        cursor.execute(" INSERT INTO users VALUES(?,?,?,?,?); ", insertions)
    except sqlite3.Error as e:
        return False
    connection.commit()
    return True

def login():
    # Returns the user email at the end of this function
    global connection, cursor
    # Here we validate a login based on the credential entered
    # Make sure to protect against injections here
    email = input("Enter a registered email address: ")
    pwd = getpass.getpass("Enter your password here: ")
    insertions = (email, pwd)
    try:
        # Run our query to check if the user/password combination is in the db
        cursor.execute(" SELECT * FROM users WHERE email LIKE ? and pwd = ?; ", insertions)
    except sqlite3.Error as e:
        print(" SQL Error occured:", e.args[0])
        return None
    # Gather the results of the query
    result = cursor.fetchone()
    if(result != None):
        if(result[0].upper() == email.upper() and result[2] == pwd):
            print("Login successful!")
            print("Logged in as:", email.lower())
    else:
        print("Login NOT successful!")
        email = None
    connection.commit()
    return email


def search_for_sales():
    # Get user input for sale keywords, then search sales with those keywords associated to their descriptions -> Returns active sale set
    global connection, cursor
    # Get user input
    keyword_list = input("Enter key words here, separated by a space: ").split()
    # Build the first half of the query
    query = '''SELECT s.sid, s.descr, s.rprice, strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60 
FROM sales s left outer join products p on s.pid = p.pid
WHERE s.sid not in (select  s.sid 
		from sales s, bids b
		where s.sid = b.sid)
and s.edate > date('now') and (s.descr '''
    # Add enough LIKE clauses inside the query to match athe amount of keywords entered
    i = 0
    for keyword in keyword_list:
        if i != len(keyword_list) - 1:
            query += "LIKE '%" + keyword + "%' or s.descr "
        else:
            query += "LIKE '%" + keyword + "%'"
        i += 1
    query += " or p.descr "
    # Repeat previous task
    i = 0
    for keyword in keyword_list:
        if i != len(keyword_list) - 1:
            query += "LIKE '%" + keyword + "%' or s.descr "
        else:
            query += "LIKE '%" + keyword + "%'"
        i += 1
    # Build second half of the query
    query += ''') UNION 
Select s.sid, s.descr, max(b.amount), strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60
from sales s left outer join products p on s.pid = p.pid, bids b
where s.sid = b.sid and s.edate > date('now') and (s.descr '''
    # Create enough LIKE clauses in the query again to match the amount of keywords entered
    i = 0
    for keyword in keyword_list:
        if i != len(keyword_list) - 1:
            query += "LIKE '%" + keyword + "%' or p.descr "
        else:
            query += "LIKE '%" + keyword + "%'"
        i += 1
    query += " or p.descr "
    i = 0
    # Repeat above process
    for keyword in keyword_list:
        if i != len(keyword_list) - 1:
            query += "LIKE '%" + keyword + "%' or s.descr "
        else:
            query += "LIKE '%" + keyword + "%'"
        i += 1
    # Finish query and execute results
    query += ") group by s.descr, s.sid;"
    cursor.execute(query)
    results = cursor.fetchall()
    for result in results: 
        print(result)
    connection.commit()
    return results

def place_bid(sid, user, results, connection, cursor):
    # Place a bid on a sale entered by the user (by sid)
    amount = float(input("Enter a bid amount: "))
    cursor.execute("SELECT MAX(amount) FROM bids WHERE sid = ?", (sid,))
    result = cursor.fetchone()
    connection.commit()
    # Check to make sure that the bid is high enough! (Greater than previous max bid!) -> Still need to integrate random bid generator!!
    if(result[0] == None or result[0] < amount):
        cursor.execute(''' SELECT bid FROM bids; ''')
        allIds = cursor.fetchall()
        bid_id = getNewId(allIds, cursor, connection)
        insertions = (bid_id, user, sid, amount)
        cursor.execute("INSERT INTO bids VALUES(?, ?, ?, date('now'), ?)", insertions)
        connection.commit()
        print("Bid successfully placed!")
    else:
        print("Bid amount not high enough!")
    return


def validate_sid(results, sid):
    # Validate an entered sid
    valid = False
    for result in results:
        if result[0].upper() == sid.upper():
            valid = True
            break
    return valid   

def list_active_seller_sales(lister, cursor, connection):
    # Query the data to list all the active sales of the seller of a sale!
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
    # Print out the results nicely
    for result in results:
        print(result)
    connection.commit()

def get_reviews_seller(lister, cursor, connection):
    # Query the data to get all of the reviews of a given seller of a sale!
    cursor.execute('''SELECT reviewer, rating, rtext, rdate FROM reviews WHERE reviewee LIKE ? ''', (lister,))
    results = cursor.fetchall()
    print('\n')
    for result in results:
        print(result)
    connection.commit()

# Run main
if __name__ == "__main__":
    main()
