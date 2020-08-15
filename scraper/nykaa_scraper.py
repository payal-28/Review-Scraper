from bs4 import BeautifulSoup as bs
from selenium import webdriver
import pymongo
firefox_options = webdriver.FirefoxOptions()
firefox_options.add_argument('--no-sandbox')
firefox_options.add_argument('--headless')
firefox_options.add_argument('window-size=1920,1080')
firefox_options.add_argument('--disable-gpu')
driver = webdriver.Firefox(options=firefox_options)
import warnings
warnings.filterwarnings("ignore")


def nykaa_reviews():
    search_string = input("Enter the product name to be searched: ")
    input_product = search_string.replace(" ","%20") # obtaining the input_product
    reviews = []
    try:
        dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
        db = dbConn.crawlerDB # connecting to the database called crawlerDB
        a = db[search_string].find() # searching the collection with the name same as the keyword

        if a.count() > 0: # if there is a collection with searched keyword and it has records in it
            for i in a:
                reviews.append(i)
            return reviews # show the results to user
        else:
            nykaa_url = "https://www.nykaa.com/search/result/?ptype=search&q=" + input_product  # preparing the URL to search the product on nykaa
            driver.get(nykaa_url) #using gecko driver to get the html of nykaa webpage
            driver.implicitly_wait(30)
            source = driver.page_source
            html = bs(source, "html.parser")  # parsing webpage as html
            bigboxes = html.findAll("div", {"class": "card-wrapper-container col-xs-12 col-sm-6 col-md-4"}) # seacrhing for appropriate tag to redirect to the product link
            for i in bigboxes:
                if 'tip-tile' in i.div.div['class']:        
                    bigboxes.remove(i)         # removing unnecessary boxes which include ads  
            for box in bigboxes:
                productLink = "https://www.nykaa.com" + box.div.a['href']   # extracting the actual product link
                driver.get(productLink)     # using driver again to get the html of specific product page
                driver.implicitly_wait(30)
                source = driver.page_source
                prod_html = bs(source, "html.parser") # parsing the product page as HTML
                prod_name = prod_html.find_all('h1', {'class': "product-title"}) #finding the product name
                prod_name = prod_name[0].text   
                commentboxes = prod_html.find_all('div', {'class': "col-md-12"}) # finding the HTML section containing the customer comments
                del commentboxes[0:3] # deleting unnecesaary things

                table = db[search_string] # creating a collection with the same name as search string.
                for comment in commentboxes:
                    try:
                        name = comment.find_all('span', {'class': "reviewer-name"})[0].text # finding reviewer name
                    except:
                        name = "no name"
                    try:
                        header = comment.header.find_all('h4')[0].text # finding comment heading
                    except:
                        header = "no header"
                    try:
                        rating = comment.find('meta',{'itemprop':'ratingValue'}) # finding rating value given by the reviewer
                        x = rating["content"] if rating else None
                    except:
                        x = "no rating"
                    try:
                        review = comment.find('meta',{'itemprop': 'description'}) # finding comment dexcription
                        description = review["content"] if review else None
                    except:
                        description = "no description"
                    mydict = {"Product": prod_name, "Name": name, "Rating": x, "CommentHead": header,"Comment": description} # combining all the information in a dictionary
                    y = table.insert_one(mydict) #insertig the dictionary containing the review comments to the collection
                    reviews.append(mydict) #  appending the comments to the review list
            return reviews
    except BaseException as e:
        return 'something is wrong'             
                   
nykaa_reviews()     