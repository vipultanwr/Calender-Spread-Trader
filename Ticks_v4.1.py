import logging
from kiteconnect import KiteTicker,KiteConnect
from datetime import datetime,timedelta
import pandas as pd
from math import sqrt
import os

import webbrowser
import time
import appscript

def get_sess_id():

    url = 'https://kite.trade/connect/login?api_key=kupxiilizwwmrs9m&v=3'

    chrome_path = 'open -a /Applications/Google\ Chrome.app %s'

    webbrowser.get(chrome_path).open(url)

    time.sleep(7)

    urls = appscript.app('Google Chrome').windows.tabs.URL()

    strng = urls[0][-1]
    sess_id = strng.partition('request_token=')[2]

    sess_id = sess_id.partition('&action')[0]
    print(sess_id)
    return sess_id


# Initialise

kite = KiteConnect(api_key="kupxiilizwwmrs9m")


data = kite.generate_session(get_sess_id(), api_secret="API_SECRET")
tokens = [54922503, 55168263]

kws = KiteTicker("kupxiilizwwmrs9m", data['access_token'])

# tokens = [10973954, 14451970]

TradeTableDF = pd.DataFrame(columns = ['Time','Action','SpreadValue','zscore','nearLTP','farLTP','ExactSpread','AdverseSpread'])

position = 0

nearbidprc = 0
nearbidqty = 0

nearaskprc = 0
nearaskqty = 0
farbidprc = 0
farbidqty = 0
faraskprc = 0
faraskqty = 0
nearLTP = 0
farLTP = 0

CheckforAdverseExecution = False


def print_bidaskspread(tick):


    global nearbidprc
    global nearbidqty
    global nearaskprc
    global nearaskqty
    global farbidprc
    global farbidqty
    global faraskprc
    global faraskqty
    global nearLTP
    global farLTP

    # print(tick)

    if(tick[0]['instrument_token'] == tokens[0]):

        nearLTP    = tick[0]['last_price']
        nearbidprc = tick[0]['depth']['buy'][0]['price']
        nearbidqty = tick[0]['depth']['buy'][0]['quantity']


        nearaskprc = tick[0]['depth']['sell'][0]['price']
        nearaskqty = tick[0]['depth']['sell'][0]['quantity']


    elif(tick[0]['instrument_token'] == tokens[1]):
        
        farLTP    =  tick[0]['last_price']
        farbidprc =  tick[0]['depth']['buy'][0]['price']
        farbidqty =  tick[0]['depth']['buy'][0]['quantity']

        faraskprc =  tick[0]['depth']['sell'][0]['price']
        faraskqty =  tick[0]['depth']['sell'][0]['quantity']


    if(len(tick) == 2):

        if(tick[1]['instrument_token'] == tokens[0]):

            # nearLTP    = tick[1]['last_price']
            nearbidprc = tick[1]['depth']['buy'][0]['price']
            nearbidqty = tick[1]['depth']['buy'][0]['quantity']


            nearaskprc = tick[1]['depth']['sell'][0]['price']
            nearaskqty = tick[1]['depth']['sell'][0]['quantity']

        elif(tick[1]['instrument_token'] == tokens[1]):
        
            # farLTP    = tick[1]['last_price']
            farbidprc = tick[1]['depth']['buy'][0]['price']
            farbidqty = tick[1]['depth']['buy'][0]['quantity']


            faraskprc = tick[1]['depth']['sell'][0]['price']
            faraskqty = tick[1]['depth']['sell'][0]['quantity']
        

    # global buyspread 
    # global sellspread 

    # sellspread = nearbidprc - faraskprc
    # buyspread = nearaskprc - farbidprc
    # print(nearLTP, farLTP,nearbidprc, nearaskprc,farbidprc,faraskprc)
    return nearLTP, farLTP,nearbidprc, nearaskprc,farbidprc,faraskprc

    # print("================\n")
    # print(sellspread - buyspread)

    # print("   BID        ASK\n")
    # print(str(nearbidprc) + str("        ")+str(nearaskprc) + str("\n"))
    # print(str(farbidprc) + str("        ")+str(faraskprc))
    # print("================\n")

def get_historical_hourly_candles(daydiff,tokens):

    global historic_spread
    global historic_spread_mean
    global historic_spread_std

    now = datetime.now()

    end_time   = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
    start_time = (now - timedelta(days=daydiff)).strftime("%Y-%m-%d %H:00:00")

    print(end_time)
    print(start_time)
    
    data_near = kite.historical_data(instrument_token=tokens[0],from_date=start_time,to_date=end_time,interval='hour')
    data_far  = kite.historical_data(instrument_token=tokens[1],from_date=start_time,to_date=end_time,interval='hour')

    data_near_df = pd.DataFrame(data_near)
    data_far_df  = pd.DataFrame(data_far)

    spd = data_near_df.close - data_far_df.close

    spd = spd[-4:]

    return spd, spd.mean(),spd.std()

def get_realtime_indicator(spd,spdmean,spdstd,nearLTP,farLTP,nearbidprc,nearaskprc,farbidprc,faraskprc):


    # last_spread = nearLTP - farLTP

    last_spread_long = nearaskprc - farbidprc

    last_spread_short = nearbidprc - faraskprc
    
    lastspdmean = spdmean

    spdmean_long = ((lastspdmean*4) + last_spread_long)/5

    spdmean_short = ((lastspdmean*4) + last_spread_short)/5

    spdvar = spdstd*spdstd

    spdstd_long = sqrt((((5-2)*spdvar) + ((last_spread_long-spdmean_long)*(last_spread_long-lastspdmean)))/(5-1))   #https://math.stackexchange.com/questions/775391/can-i-calculate-the-new-standard-deviation-when-adding-a-value-without-knowing-t

    spdstd_short = sqrt((((5-2)*spdvar) + ((last_spread_short-spdmean_short)*(last_spread_short-lastspdmean)))/(5-1))   #https://math.stackexchange.com/questions/775391/can-i-calculate-the-new-standard-deviation-when-adding-a-value-without-knowing-t

    last_zscore_long = (last_spread_long - spdmean_long)/spdstd_long
    last_zscore_short = (last_spread_short - spdmean_short)/spdstd_short

    print("       longspread        shortspread    ")
    print("price: ",last_spread_long,"          ",last_spread_short)
    print("                      ")
    print("zScor:  ","{0:.2f}".format(last_zscore_long),"            ","{0:.2f}".format(last_zscore_short))
    print("-----------------------------------")
    print("                      ")
    print("{0:.2f}".format(farLTP - nearLTP))

    #if(last_spread_long < -980):
        #do nothing

    return last_spread_long,last_spread_short,last_zscore_long,last_zscore_short

def zscore(x, window):
    r = x.rolling(window=window)
    m = r.mean().shift(1)
    s = r.std(ddof=0).shift(1)
    z = (x-m)/s
    return z.fillna(0)

#################################################################

def on_ticks(ws, ticks):

    global historic_spread
    global historic_spread_mean
    global historic_spread_std

    global position
    
    global TradeTableDF

    # global nearbidprc
    # global nearbidqty
    # global nearaskprc
    # global nearaskqty
    # global farbidprc
    # global farbidqty
    # global faraskprc
    # global faraskqty
    global nearLTP
    global farLTP

    global CheckforAdverseExecution

    global positionOpenTime
    global timeSinceLastPositionOpen

    nearLTP, farLTP, nearbidprc, nearaskprc, farbidprc, faraskprc = print_bidaskspread(ticks)
    
    curr_time = datetime.now()

    if((curr_time.second == 0) & (curr_time.minute == 0)):
        historic_spread,historic_spread_mean,historic_spread_std =  get_historical_hourly_candles(7,tokens)  #moved 100 to 50 as reduced trading hours in a day

        print('change of hour observed, getting historical data...')
    
    last_spread_long,last_spread_short,last_zscore_long,last_zscore_short = get_realtime_indicator(historic_spread,historic_spread_mean,historic_spread_std,nearLTP,farLTP,nearbidprc,nearaskprc,farbidprc,faraskprc)

    if(position != 0):
        timeSinceLastPositionOpen = curr_time - positionOpenTime
        print(timeSinceLastPositionOpen.seconds)


    if (CheckforAdverseExecution == True):

        previousAction = TradeTableDF.loc[len(TradeTableDF)-1]['Action']
        AdverseSpread = 0
        if((previousAction == 'ShortEntry')|(previousAction == 'LongExit')):

            AdverseSpread = nearbidprc - faraskprc

        elif ((previousAction == 'ShortExit')|(previousAction == 'LongEntry')):

            AdverseSpread = nearaskprc - faraskprc


        TradeTableDF.at[len(TradeTableDF)-1,'AdverseSpread'] = AdverseSpread

        CheckforAdverseExecution = False


        if(len(TradeTableDF) > 0):    
            TradeTableDF.to_csv("TradeTable.csv",mode='a',header='none')


    longentryScore = -0.5
    shortentryScore =  0.5
    longexitScore = -0.5
    shortexitScore = 0.5

    if((position != 0)):   #http://fooplot.com/
        
        if(timeSinceLastPositionOpen.seconds < 1500):
        
            longexitScore =  max(-((1500/(1500-(timeSinceLastPositionOpen.seconds))) -1 )*0.1,-0.5) 
        
        
            shortexitScore =  min(((1500/(1500-(timeSinceLastPositionOpen.seconds))) -1 )*0.1,0.5)




    print(longexitScore)

    if((nearbidprc > 0) & (nearaskprc > 0) & (farbidprc > 0) & (faraskprc > 0) & (nearLTP > 0) & (farLTP > 0)):
        if((position == 0) & (last_zscore_short > shortentryScore)):

            entrylist = [curr_time,'ShortEntry',last_spread_short,last_zscore_short,nearLTP,farLTP,nearbidprc - faraskprc,0]
            TradeTableDF.loc[len(TradeTableDF)] = entrylist
            position = -1
            
            print("SHORT POSITION OPENED")
            os.system("say SHORT POSITION OPENED")
            
            CheckforAdverseExecution = True

            positionOpenTime =  datetime.now()



        elif((position == 0) & (last_zscore_long < longentryScore)):

            entrylist = [curr_time,'LongEntry',last_spread_long,last_zscore_long,nearLTP,farLTP,nearaskprc - farbidprc,0]
            TradeTableDF.loc[len(TradeTableDF)] = entrylist
            position = 1
            
            print("LONG POSITION OPENED")
            os.system("say LONG POSITION OPENED")

            CheckforAdverseExecution = True

            positionOpenTime =  datetime.now()



        elif((position == 1) & (last_zscore_short > longexitScore)):

            entrylist = [curr_time,'LongExit',last_spread_short,last_zscore_short,nearLTP,farLTP,nearbidprc - faraskprc,0]
            TradeTableDF.loc[len(TradeTableDF)] = entrylist
            position = 0
            
            print("LONG POSITION CLOSED")
            os.system("say LONG POSITION CLOSED")

            CheckforAdverseExecution = True



        elif((position == -1) & (last_zscore_long < shortexitScore)):

            entrylist = [curr_time,'ShortExit',last_spread_long,last_zscore_long,nearLTP,farLTP,nearaskprc - farbidprc,0]
            TradeTableDF.loc[len(TradeTableDF)] = entrylist
            position = 0
            
            print("SHORT POSITION CLOSED")
            os.system("say SHORT POSITION CLOSED")

            CheckforAdverseExecution = True




def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(tokens)

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, tokens)

    global historic_spread
    global historic_spread_mean
    global historic_spread_std

    historic_spread,historic_spread_mean,historic_spread_std =  get_historical_hourly_candles(7,tokens)
    print("connected successfully!")
    print(historic_spread,historic_spread_mean,historic_spread_std)

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    os.system("say CONNECTION CLOSED")

    global TradeTableDF
    # TradeTableDF.to_csv('TradeTable.csv')

    data = kite.generate_session(get_sess_id(), api_secret="API_SECRET")
    # ws.stop()

#################################################################

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()



