import sqlite3
import time
from setup import *
from saleInfo import *

def list_product(cursor, connection, email):
    # This function executes a query that gets all the products associated to active sales! -> Then provides further instructions to the user for actions that they can perform

    

    listProduct_query = ''' SELECT distinct p.pid, p.descr, COUNT(pr.rtext), AVG(pr.rating), COUNT(distinct s.sid)
                            FROM products p inner join sales s on s.pid = p.pid and s.edate > DATE('now') 
                            LEFT OUTER JOIN previews pr ON p.pid = pr.pid 
                            group by p.pid
                 	    order by count(distinct s.sid) DESC;

                        '''    

    cursor.execute(listProduct_query)

    productList = cursor.fetchall()
 

    if len(productList) > 1:

        for product in productList:

            print(product)
            isTrue = True

    #if there is no productList, then there's no product to perform additional actions on.       
    else: 
        isTrue = False
        return

    while(isTrue):
        
        isTrue = False

        command = input(''' Enter the following key for the corresponding functions

                        a - to write a review

                        b - to view reviews of a product

                        c - to view all active sales associated to the product

                    ''')

        

        #if more than 1 character/command entered(Error)                

        if(len(command) > 1):

            print('Invalid command, try again')
            
            isTrue = True

            continue #goes to end of loop

        

        #if invalid character(not 'a','b' or 'c') entered

        if(command != 'a' and command != 'b' and command != 'c'): ##check

            print('Invalid Command')
            
            isTrue = True

            continue #goes to end of loop

        

        #check for what command is entered and take actions accordingly 

        if(command == 'a'):

           productId = input('''Please enter the pid of the product that you wish to write a review on: ''')


           write_review(productList,productId, cursor, connection, email)

        

        if(command == 'b'):

           productId = input('''Please enter the pid of the product you wish to view:  ''')

           view_review(productList,productId, cursor, connection)

        

        if(command == 'c'):

           productId = input('Please enter the pid of the product that you want to see the sales associated with it: ')

           view_activeSales(productList,productId, cursor, connection, email)

    connection.commit()


#function that allows to view review on the product listed 
def view_review(productList,pid, cursor, connection):

    isExists = False

    print(pid)
    #checks if the pid entered by the user is a valid pid from the productList
    for each in productList:


        if( pid == each[0]):

            isExists = True

            break

        
    if(isExists):

        cursor.execute(''' SELECT pr.rid, pr.pid, pr.reviewer, AVG(pr.rating), pr.rtext, pr.rdate 

                           FROM products p, previews pr
                           
                           WHERE p.pid = pr.pid
                           AND pr.pid LIKE ?
                           group by pr.rid, pr.pid, pr.reviewer, pr.rtext, pr.rdate;
                        ''', (pid,))

        
        result = cursor.fetchall()
    
        for each in result:
            print(each)
            
        
    else:

        print("Wrong Pid entered")

    connection.commit()

    

    

    
#function that allows users to write reviews on their chosen product
def write_review(productlist,pid, cursor, connection, email):


    userReview = input("Enter a review text: ")
    userRating = int(input("Enter a rating(between 1 - 5 inclusive): "))


    for each in productlist:

        if( pid == each[0]):

            isExists = True

            break

        
    
    if(isExists):

        cursor.execute(''' SELECT rid FROM previews; ''')
        allIds = cursor.fetchall()
        new_rid = getNewId(allIds, cursor, connection)
        if(userRating >= 1 and userRating <= 5):

            cursor.execute(''' INSERT INTO previews VALUES

            (?,?,?,?,?,Date('now'));''', (new_rid, pid, email, userRating, userReview))
            
                
            result = cursor.fetchall()
    
            for each in result:
                print(each)

                                    

        else:
            print("Invalid rating entered")

    connection.commit()



#function that allows to view active sales associated to the product 
#then asks the user if they want to see more info on the active sales listed 
def view_activeSales(productList,pid, cursor, connection, email): 


    isExists = False

    for each in productList:

        if( pid == each[0]):

            isExists = True 

            break

            
    
    if(isExists):

        activeSales = cursor.execute('''SELECT s.sid, s.descr, s.rprice, strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60 
FROM sales s, products p
WHERE s.sid not in (select  s.sid 
		from sales s, bids b
		where s.sid = b.sid)
and edate > date('now') and s.pid = ?
UNION 
Select s.sid, s.descr, max(b.amount), strftime('%s',s.edate) / 86400 - strftime('%s','now') / 86400, strftime('%s',s.edate) / 3600 - strftime('%s','now') / 3600, strftime('%s',s.edate) / 60 - strftime('%s','now') / 60
from sales s, bids b, products p 
where s.sid = b.sid and edate > date('now') and s.pid = ?
group by s.descr, s.sid order by strftime('%s',s.edate) / 60 - strftime('%s','now') / 60''',(pid, pid))

 
            
        result = cursor.fetchall()
    
        for each in result:
            print(each)
    
        choice4 = input("Do you want to see more info about a sale? (y/n)")
        if(choice4 == 'y'):
            moreInfo_q1(result, email, cursor, connection)
        connection.commit()
        return;

        

    else:
        print("Wrong Pid entered")

    return
            
def moreInfo_q1(results, user, cursor, connection):
    # Gets more information about a certain sale!
    ''' including the email of the lister, the rating of the lister (which includes the number of reviews and the average rating), the sale description, the sale end date and time, the condition, and the maximum bid or the reserved price (if there is no bid). If the sale is associated to a product, the result will also include the product description and the product rating, which includes the number of reviews and the average rating if available or a text that the product is not reviewed
    '''
    # check if its accurate
    chosenSid = input("What sales do you want to know more information about?: ")
    valid = validate_sid_q1(results, chosenSid)
    if(not valid):
        print("Invalid sid")
        return False
    # Query the data
    cursor.execute('''select sales.lister, COUNT(reviews.rating), AVG(reviews.rating), sales.descr, sales.edate, sales.cond, sales.rprice, products.descr, COUNT(previews.rating), AVG(previews.rating)  
FROM sales left outer join reviews on reviews.reviewee = sales.lister, products left outer join previews on previews.pid = products.pid
WHERE sales.sid not in (select  sales.sid 
		from sales, bids
		where sales.sid = bids.sid)
and edate > date('now')
and sales.sid LIKE ?
and products.pid = sales.pid
group by sales.lister, sales.descr, sales.edate, sales.cond, sales.rprice, products.descr
UNION 
select sales.lister, COUNT(reviews.rating), AVG(reviews.rating), sales.descr, sales.edate, sales.cond, max(bids.amount), products.descr, COUNT(distinct previews.rating), AVG(previews.rating)  
from sales left outer join reviews on sales.lister = reviews.reviewee, bids, products left outer join previews on products.pid = previews.pid
where sales.sid = bids.sid and edate > date('now')
and sales.sid LIKE ?
and products.pid = sales.pid
group by sales.lister, sales.descr, sales.edate, sales.cond, products.descr; 

''',(chosenSid,chosenSid))
    # Get results table and format
    results = cursor.fetchall()
    print('\nColumns (Top to bottom):\nLister | Num ratings | AVG rating | descr | edate | cond | price | Max bid | pdesc | Num previews | AVG prating\n')
    for info in results:
        for test in info:
            if(test == None):
                print("There are no product reviews")
            else:
                print(test)
    print("", end = '\n')
    connection.commit()
    # Give user choice on what to do next! -> Bid, list active seller sale, see reviews of the seller!
    choice3 = input("Would you like to place a bid? (1) List all active sales of the seller (2) or List all reviews of the seller? (3): ")
    if(choice3 == '1'):
        place_bid_q1(chosenSid, user, results, connection, cursor)
    elif(choice3 == '2'):
        cursor.execute('''SELECT distinct lister from sales where sid LIKE ?''', (chosenSid,))
        result = cursor.fetchone()
        email = result[0]
        list_active_seller_sales_q1(email, cursor, connection)
    elif(choice3 == '3'):
        cursor.execute('''SELECT distinct lister from sales where sid LIKE ?''', (chosenSid,))
        result = cursor.fetchone()
        email = result[0]
        get_reviews_seller_q1(email, cursor, connection)
    else:
        return
    return True

def validate_sid_q1(results, sid):
    # Validate an entered sid
    valid = False
    for result in results:
        if result[0].upper() == sid.upper():
            valid = True
            break
    return valid  
    
def place_bid_q1(sid, user, results, connection, cursor):
    # Place a bid on a sale entered by the user (by sid)
    amount = float(input("Enter a bid amount: "))
    cursor.execute("SELECT MAX(amount) FROM bids WHERE sid LIKE ?", (sid,))
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

def list_active_seller_sales_q1(lister, cursor, connection):
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
    for result in results:
        print(result)
    connection.commit()

def get_reviews_seller_q1(lister, cursor, connection):
    # Query the data to get all of the reviews of a given seller of a sale!
    cursor.execute('''SELECT reviewer, rating, rtext, rdate FROM reviews WHERE reviewee LIKE ? ''', (lister,))
    results = cursor.fetchall()
    print('\n')
    for result in results:
        print(result)
    connection.commit()



    

    

    

	

    


