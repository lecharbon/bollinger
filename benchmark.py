#coding: utf-8

import requests
import time
from datetime import datetime
import csv
import os


from pandas import *
import talib

#----------------------------------------------------------------------------------------------------------------------------------------------------------------

#pairs = ['tBTCUSD', 'tETHUSD', 'tXMRUSD', 'tLUNA:USD', 'tSOLUSD', 'tADAUSD', 'tAVAX:USD', 'tMATIC:USD']
#pairs = ['tLUNA:USD']
pairs = ['tBTCUSD', 'tETHUSD', 'tXMRUSD', 'tADAUSD']


timeframes = ['1h','3h','1D']
nb_periods = '300'


def get_data_bitfinex(pair, timeframe):
    try:
        response = requests.get("https://api-pub.bitfinex.com/v2/candles/trade:"+ timeframe + ":" + pair + "/hist?limit=" + nb_periods + "&end=1545157427000")
        rawData = response.json()
        return rawData
    except:
        print('Request error Bitfinex')
        time.sleep(2)
        return {'error': True}


#----------------------------------------------------------------------------------------------------------------------------------------------------------------

# Il faudrait calculer le risque max


def main(pair, percent, timeframe):
    benef = 1
    risk_max = 0
    benef_short = 1
    risk_max_short = 0

    # Prepare DataFrame
    rawData = get_data_bitfinex(pair, timeframe)[::-1]
    pandas.set_option('display.max_rows', None)

    df = pandas.DataFrame(rawData)
    df.columns = ['time','open','close','high','low','volume']
    df['upper'], df['middle'], df['lower'] = talib.BBANDS(df['close'], timeperiod=20)
    df = df.tail(int(df.shape[0])-20)
    df['date'] = [datetime.fromtimestamp(x/1000) for x in df['time']]
    df.reset_index(inplace= True, drop=True)
    #print(df)

    # Check Strategy on short side (overextended up)
    for index, row in df.iterrows():
        if (row['upper']*(1 + percent/100) < row['high']):
            # Does it go back within the bands in the same period?
            if (row['close'] < row['upper']):
                benef = benef * (1 + percent/100)
                #if risk_max < (1 + percent/100)
                #print(datetime.fromtimestamp(row['time']/1000) ,': long - prise de benef sur ', pair, ' en ', timeframe,' de ', str(1 + percent/100) , ' (',percent,'%)')
                #print(datetime.fromtimestamp(row['close']) , ' : transaction within same period')
            else :
                i = 0
                # Loop to find when it goes back within BBands
                is_not_within = True
                while is_not_within:
                    # Tant que le low est supérieur à la BB...
                    if (df.iloc[index+i]['upper'] < df.iloc[index+i]['low']):
                        i += 1
                    else:
                        new_benef = (row['upper']*(1 + percent/100)) / df.iloc[index+i]['upper']
                        #print('Transaction after ', i , ' periods. Benef: ', new_benef)
                        benef = benef * new_benef
                        is_not_within = False
                        #print(datetime.fromtimestamp(row['time']/1000) ,': long - prise de benef sur ', pair, ' en ', timeframe,' de ', new_benef)
                        #print('entrée: ', str(row['upper']*(1 + percent/100)) , ' / sortie: ' , df.iloc[index+i]['upper'] ,' à ', df.iloc[index+i]['time'])
                        #print(df.loc[[index+i+2, index+i+1, index+i, index+i-1, index+i-2]])

        if (row['lower']*(1 - percent/100) > row['low']):
            # Does it go back within the bands in the same period?
            if (row['close'] > row['lower']):
                benef_short = benef_short * (1 + percent/100)
                #print(datetime.fromtimestamp(row['time']/1000) ,': short - prise de benef sur ', pair, ' en ', timeframe,' de ', str(1 + percent/100))

                #print(datetime.fromtimestamp(row['close']) , ' : transaction within same period')
            else :
                i = 0
                # Loop to find when it goes back within BBands
                is_not_within = True
                while is_not_within:
                    # Tant que le low est supérieur à la BB...
                    if (df.iloc[index+i]['lower'] > df.iloc[index+i]['high']):
                        i += 1
                    else:
                        new_benef = df.iloc[index+i]['lower'] / (row['lower']*(1 - percent/100))
                        #print('Transaction after ', i , ' periods. Benef: ', new_benef)
                        benef_short = benef_short * new_benef
                        #print(datetime.fromtimestamp(row['time']/1000))
                        is_not_within = False
                        #print(datetime.fromtimestamp(row['time']/1000) ,': short - prise de benef sur ', pair, ' en ', timeframe,' de ', new_benef)

    print(pair ,' / ', timeframe, ': ', benef ,'% de perf avec ', percent , '%')
    print(pair ,' / ', timeframe, ': ', benef_short ,'% de perf avec ', percent , '% (SHORT)')
    outfile = open("raw_data.csv","a")
    writer = csv.writer(outfile)
    writer.writerow([pair, timeframe, percent, benef, 'long'])
    writer.writerow([pair, timeframe, percent, benef_short, 'short'])


for pair in pairs:
    for timeframe in timeframes:
        percent = 4
        while percent<20:
            main(pair, percent, timeframe)
            time.sleep(1)
            percent +=1




#
