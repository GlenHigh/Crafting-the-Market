from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import openpyxl
import time
import datetime
import os
os.chdir('/Users/glenhigh/PycharmProjects/BazaarTracker')

#Kill all headless drivers
os.system("pkill -f \"(chrome)?(--headless)\"")


 #List to store name of the product
 #List to store price of the product
IS_SCRAPPED=False
HOURS_TO_RUN=10
FREQUENCY_IN_MINS=1
VERBOSE=True
SAVE_TO_CSV = False

print("Start...")

if IS_SCRAPPED==False:
    #driver = webdriver.Chrome(executable_path='/Users/glenhigh/PycharmProjects/BazaarTracker/chromedriver')
    chrome_options = Options()
    #options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path='/Users/glenhigh/PycharmProjects/BazaarTracker/chromedriver', options=chrome_options)
    print("Driver ok...")
    IS_SCRAPPED=True


start_time = time.time()
end_time = HOURS_TO_RUN*3600+start_time

full_table=[["Index","Date","Ask_Volume_3","Ask_Price_3","Ask_Volume_2","Ask_Price_2","Ask_Volume_1","Ask_Price_1","Bid_Volume_1","Bid_Price_1","Bid_Volume_2","Bid_Price_2","Bid_Volume_3","Bid_Price_3"]]
counter=1

print("Looping...")

while(time.time()<end_time):

    #init what we'll need (scrape tables)
    driver.get("https://bazaartracker.com/product/gold_ingot")
    content = driver.page_source
    soup = BeautifulSoup(content)

    buy_table = soup.find("table", {'id': 'buyorderstbl'})
    sell_table = soup.find("table", {'id': 'sellorderstbl'})

    buy_table_body = buy_table.find('tbody')
    sell_table_body = sell_table.find('tbody')
    line=[]#our line of data

    #1: get date
    begin = time.time()
    line.append(counter)
    line.append(int(time.time()))

    #2: get ask in format Vol10;Price10;Vol9;Price9;....Vol1;Price1

    i = 3
    for row in sell_table_body.findAll("tr")[:3][::-1]:  # here i revert the array to sort prices decreasingly
        cells = row.findAll("td")
        cells = [ele.text.strip() for ele in cells]
        if "k" in cells[0]:
            cells[0] = int(float(cells[0].replace('k', '')) * 1000)
        elif "m" in cells[0]:
            cells[0] = int(float(cells[0].replace('m', '')) * 1000000)
        cells[1] = float(cells[1].replace(" coins", ""))
        if(VERBOSE):
            print("Ask ", i, " volume : ", cells[0], " price : ", cells[1], " coins")
        line.append(int(cells[0]))#add to our data
        line.append(float(cells[1]))
        i = i - 1
    print("===================================")
    #3: same for bid
    i = 1
    for row in buy_table_body.findAll("tr")[:3]:
        cells = row.findAll("td")
        cells = [ele.text.strip() for ele in cells]
        if "k" in cells[0]:
            cells[0] = int(float(cells[0].replace('k', '')) * 1000)
        elif "m" in cells[0]:
            cells[0] = int(float(cells[0].replace('m', '')) * 1000000)
        cells[1] = float(cells[1].replace(" coins", ""))
        if(VERBOSE):
            print("Bid ", i, " volume : ", cells[0], " price : ", cells[1], " coins")
        line.append(int(cells[0]))#add to our data
        line.append(float(cells[1]))
        i = i + 1
    it_worked=True
    #sometimes, data isn't fetched by my soup... so just don't add garbage to data!
    if(len(line)!=14):
        print("BREACH : Iter ", counter, " NOT ok :")
        print(line)
        print(len(line),"    ", len(full_table[0]))
        counter=counter-1#nope this never happened!
        it_worked=False
    else:
        wb = openpyxl.load_workbook("CompactBazaarOrderBookData.xlsx")
        ws = wb['Data']
        ws.append(line[1:])
        wb.save("CompactBazaarOrderBookData.xlsx")
        full_table.append(line)  # add line to table
        print("Iter ", counter, " ok")

    if(it_worked):
        temp =time.time()
        while(temp<begin+FREQUENCY_IN_MINS*60):
            time.sleep(0.1)
            temp = time.time()
        #sleep before next step
    counter=counter+1



full_table=np.array(full_table)
if(VERBOSE):
    print(full_table)


if(SAVE_TO_CSV):
    df = pd.DataFrame(data=full_table[1:, 1:], index=full_table[1:, 0], columns=full_table[0, 1:])

    print("Writing csv...")
    title = "CompactBazaarOrderBook_" + '{date:%Y-%m-%d_%Hh%Mm%Ss}'.format(
        date=datetime.datetime.now()) + '_Freq_' + str(FREQUENCY_IN_MINS) + 'min_' + 'Dur' + str(
        HOURS_TO_RUN) + 'hrs' + '.csv'
    df.to_csv(title, index=False, encoding='utf-8')
    print("csv written")

    print("Closing driver...")
    driver.close
    print("Driver closed")


#Kill all headless drivers... to be sure !
os.system("pkill -f \"(chrome)?(--headless)\"")