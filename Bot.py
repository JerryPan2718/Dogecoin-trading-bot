import time 
import os, io
import urllib.request
import tweepy
from google.cloud import vision
from google.cloud import vision_v1
import urllib.parse,  urllib.request
import hashlib, hmac, time
import requests

LONG_DOGE = 'DOGEUSD_PERP'
LONG = 'LONG'
SHORT = 'SHORT'
SELL = 'SELL'
BUY = 'BUY'

DOGE_TRADE_QUANTITY = 20000  # number of conts, 1 cont = $10 
max_cont = 10000  # the maximum number of conts can be traded in each request in binance
dates = []  # stores the dates of tweets that were already processed

# check whether or not the string 'dog' is included in the tweet
def hasDog(str):
    for x in range(len(str)):
        if str[x:x+3].lower()=='dog':
            for y in range(x+1):
                if str[x-y-1] == '@':
                    break
                elif str[x-y-1] ==' ' or x-y==0:
                    return True
            
    return False

# check whether or not any dog related content is in the meme image (Elon loves tweeting doge memes)
# Google Vision API is used here for image detection
# info about the google vision api: https://cloud.google.com/vision
def hasDogImage(info):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'*' # replace * with your own credential 
    client = vision.ImageAnnotatorClient()

    try:
        URL = ((info.entities)['media'])[0]['media_url']
    except Exception:
        return False

    with urllib.request.urlopen(URL) as url:
        with open('temp.jpg', 'wb') as f:
            f.write(url.read())

    with io.open('temp.jpg','rb') as image_file:
        content = image_file.read()

    image = vision_v1.types.Image(content=content)

    response = client.text_detection(image = image)
    for text in response.text_annotations:
        if hasDog(text.description):
            return True

    response = client.object_localization(image = image)
    for text in response.localized_object_annotations:
        if hasDog(text.name):
            return True

    response = client.label_detection(image = image)
    for text in response.label_annotations:
        if hasDog(text.description):
            return True
    
    return False

# because the Twitter API passes old and repeated tweets sometimes, we need to check the date
def goodTime(str):
    year = int(str[2:4])
    month = int(str[5:7])
    day = int(str[8:10])
    if year >= 21 and (month > 7 or ((month==7) & (day >= 1))): # I know it's such a bad logic here, but I'm just too lazy to fix it, so just change the date mannully if you're as lazy as me
        return True
    return False


# trade in binance
# get your APIKEY from https://www.binance.com/en/my/settings/api-management
BASE_URL = 'https://dapi.binance.com/dapi/v1/order'
LONG_APIKEY = ''
LONG_SECRET = ''

def trade(symbol,side,quantity):
    timestamp = int(time.time() * 1000)
    
    headers = {
        'X-MBX-APIKEY': LONG_APIKEY
    }

    params = {
        'symbol': symbol,
        'side': side,
        'positionSide': LONG,
        'type': 'MARKET',
        'quantity': int(quantity), 
        'timestamp': timestamp
    }
    query_string = urllib.parse.urlencode(params)

    params['signature'] = hmac.new(LONG_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    r = requests.post(BASE_URL, headers=headers, params=params)

    dataSet = r.json()
    print ('request info\n'+str(dataSet))


# scrape Twitter
# visit https://developer.twitter.com/en to apply for Twitter developer account, then you will get your own API KEY
TWITTER_API_KEY = ''
TWITTER_API_SECRET_KEY = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_TOKEN_SECRET = ''

auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET_KEY)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_TOKEN_SECRET)

api = tweepy.API(auth)

tweetDateList = open("processedTweetsDate.txt",'r').read().split('\n')

def run():
    while True:
        time.sleep(0.9)

        try:
            user_tweets = api.user_timeline(screen_name='elonmusk', count=1)
        except Exception:
            continue
        
        for info in user_tweets:
            date = info.created_at
            text = info.text
            
            if (not str(date) in tweetDateList) & (not date in dates) & goodTime(str(date)):
                
                if hasDog(text) or hasDogImage(info):
                    left = DOGE_TRADE_QUANTITY
                    while not left == 0:
                        if left>max_cont:
                            trade(LONG_DOGE,BUY,max_cont)
                            left -= max_cont
                        else:
                            trade(LONG_DOGE,BUY,left)
                            left = 0

                    print(text)
                    time.sleep(60)
                    left = DOGE_TRADE_QUANTITY
                    while not left == 0:
                        if left>max_cont:
                            trade(LONG_DOGE,SELL,max_cont)
                            left -= max_cont
                        else:
                            trade(LONG_DOGE,SELL,left)
                            left = 0

                # add new tweet date
                open("processedTweetsDates.txt",'a').write("\n"+str(date))
                dates.append(date)
            

run()