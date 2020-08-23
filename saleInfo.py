import sqlite3
import datetime
from setup import *
from saleUser import *

def moreInfo(results, user, cursor, connection):
    # Gets more information about a certain sale!
    ''' including the email of the lister, the rating of the lister (which includes the number of reviews and the average rating), the sale description, the sale end date and time, the condition, and the maximum bid or the reserved price (if there is no bid). If the sale is associated to a product, the result will also include the product description and the product rating, which includes the number of reviews and the average rating if available or a text that the product is not reviewed
    '''
    # check if its accurate
    chosenSid = input("What sales do you want to know more information about?: ")
    valid = validate_sid(results, chosenSid)
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
and sales.sid = ?
and products.pid = sales.pid
group by sales.lister, sales.descr, sales.edate, sales.cond, sales.rprice, products.descr
UNION 
select sales.lister, COUNT(reviews.rating), AVG(reviews.rating), sales.descr, sales.edate, sales.cond, max(bids.amount), products.descr, COUNT(distinct previews.rating), AVG(previews.rating)  
from sales left outer join reviews on sales.lister = reviews.reviewee, bids, products left outer join previews on products.pid = previews.pid
where sales.sid = bids.sid and edate > date('now')
and sales.sid = ?
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
        place_bid(chosenSid, user, results, connection, cursor)
    elif(choice3 == '2'):
        cursor.execute('''SELECT distinct lister from sales where sid = ?''', (chosenSid,))
        result = cursor.fetchone()
        email = result[0]
        list_active_seller_sales(email, cursor, connection)
    elif(choice3 == '3'):
        cursor.execute('''SELECT distinct lister from sales where sid = ?''', (chosenSid,))
        result = cursor.fetchone()
        email = result[0]
        get_reviews_seller(email, cursor, connection)
    else:
        return
    return True


