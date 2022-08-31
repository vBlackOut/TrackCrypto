from colorama import Fore, Back, Style
from forex_python.converter import CurrencyRates
from decimal import Decimal
import datetime
import numpy as np
import yfinance as yf
import time
import json
import os
import re
import pandas as pd

clear = lambda: os.system('clear')

pretty_print = lambda x: np.format_float_positional(x, trim='-')

def remove_tail_dot_zeros(a):
    tail_dot_rgx = re.compile(r'(?:(\.)|(\.\d*?[1-9]\d*?))0+(?=\b|[^0-9])')

    return pretty_print(Decimal(tail_dot_rgx.sub(r'\2', a).rstrip('0').rstrip('.')).normalize())

def percentage(percent, whole):
    return (percent * whole) / 100.0

def calcul_percent(number, diff, delta=0):

    percent = ((number*100) /diff)-delta

    if percent > 0:
        return "+{:.2f}".format(round(percent, 2))
    else:
        return round(percent, 2)

def get_percentage_diff(previous, current):
    try:
        percentage = abs(previous - current)/max(previous, current) * 100
    except ZeroDivisionError:
        percentage = float('inf')
    if previous < current:
        return -round(percentage, 2)
    else:
        return "+{:.2f}".format(round(percentage, 2))

while 1:
    clear()
    c = CurrencyRates()
    try:
        EUR_USD = round(c.get_rate('USD', 'EUR'), 5)
    except:
        EUR_USD = 1

    file = []
    with open('config.json') as f:
        # print(f.readlines())
        for line in f:
            file.append(line.replace("\'", "\""))

    file = " ".join(file)
    dict_order = json.loads(file)
    #dict_order['USDT']["1"]["prix_begin"] = EUR_USD

    dict_current_price = {}

    for key, value in dict_order.items():
        if key != "USDT":
            print("download value {}".format(key))
        if key == "USDT":
            dict_current_price[key] = dict_order[key]["1"]["prix_begin"]
        result = {}

        if key != "USDT":
            data = yf.Ticker(key)
            today_data = data.history(interval="30m", period='1d',  progress=False)

            # price = yf.download(
            #         tickers = key,
            #         period = "1d",
            #         interval = "1m",
            #         group_by = 'ticker',
            #         auto_adjust = False,
            #         prepost = False,
            #         threads = False,
            #         proxy = None
            #     )
            #
            # if len(price) == 0:
            #     continue


        # for ii, (key_price, value_price) in enumerate(price.items()):
        #
        #     list_value = []
        #
        #     if value_price.to_string().split("\n")[1].split("   ")[1] != "":
        #
        #         for i, data in enumerate(value_price.to_string().split("\n")):
        #             #if key != "USDT":
        #             if len(data.split("   ")) == 2:
        #                 list_value.append(data.split("   ")[1])
            price_series = pd.Series(today_data['Close'])
            #percent_change_today = float(get_percentage_diff((max(today_data['Close'])-min(today_data['Close'])), today_data['Close'][-1]))
            if len(today_data['Close']) <= 1 :
                # print("Waiting data collecting")
                count = 0
                while 1:
                    today_data = data.history(interval="15m", period='1d',  progress=True)
                    if len(today_data['Close']) <= 1:
                        if count %2:
                            print(".", end="\r")
                        else:
                            print("collect data please wait{}".format("."*int((count-(0.5*count)))), end="")
                        time.sleep(2)
                        count += 1
                    else:
                        break
            percent_change_today =  round(100--get_percentage_diff((max(today_data['Close'])-min(today_data['Close'])), today_data['Close'][-1]), 2)
            #print(percent_change_today)
            dict_current_price[key] = {'now': today_data['Close'][-1], "percent": calcul_percent(today_data['Close'][-1], today_data['Close'][1], 100),  "high_today": max(today_data['Close']), "low_today": min(today_data['Close']), "percent_change": percent_change_today}
                    # print(dict_current_price)
                    #break
            #break

    print()
    print("Valeurs des investissements")

    total_gain = 0
    total_investi = 0
    total_argent_ajd = 0

    for key_currency, value_currency in dict_order.items():

        if key_currency not in dict_current_price.keys():
            continue

        for key_number, value_number in value_currency.items():
            if key_number == "config":
                config = value_number
            else:
                somme_investi = value_number['solde'] * value_number['prix_begin']

                if "USD" in key_currency:
                    somme_ajd = (EUR_USD * float(dict_current_price[key_currency]['now'])) * value_number['solde']
                elif "USDT" not in key_currency:
                    somme_ajd = float(dict_current_price[key_currency]['now']) * value_number['solde']
                else:
                    somme_ajd = value_number['solde'] * float(dict_current_price[key_currency]['now'])

                gain = somme_ajd - somme_investi
                total_gain += gain
                total_investi += somme_investi
                total_argent_ajd += somme_ajd

                percent_mise = calcul_percent(gain, somme_investi)
                percent_today = calcul_percent(float(dict_current_price[key_currency]['now']), float(dict_current_price[key_currency]['high_today']))
                print()

                if "+" in str(percent_mise):
                    color = Back.GREEN+Fore.WHITE
                else:
                    color = Back.RED+Fore.WHITE


                percent_change = dict_current_price[key_currency]["percent"]

                if float(percent_mise) > 0:
                    text_gain = Back.GREEN+Fore.WHITE+"gain de "
                else:
                    text_gain = Back.RED+Fore.WHITE+"perte de "
                print("- ", key_currency,
                      "investie : {} €".format(round(somme_investi, 2)),
                      " prix ajd : {} €".format(round(somme_ajd, 2)),
                      " gain : {} €".format(round(gain, 2)),
                      "{}{}%{}".format(text_gain, percent_mise, Style.RESET_ALL),
                      "\n    prix ajd: {}{} ({} %) max: {} min: {}\n    quantité: {:,}".format(
                                        remove_tail_dot_zeros(str(float(round(dict_current_price[key_currency]['now'],
                                                                              config['float'])))),
                                                                              config['devise'],
                                                                              percent_change,
                                                                              remove_tail_dot_zeros(str(float(round(dict_current_price[key_currency]["high_today"],
                                                                                                                    config['float'])))),
                                                                              remove_tail_dot_zeros(str(float(round(dict_current_price[key_currency]["low_today"],
                                                                                                                  config['float'])))),
                                                                              value_number['solde']))

    print()
    print("Total investie : {} €\nargent ajd : {} €".format(round(total_investi, 2), round(total_argent_ajd, 2)))

    if total_gain > 0:
        print("Total gain : {}+ {} €{}".format(Back.GREEN+Fore.WHITE, round(total_gain, 2), Style.RESET_ALL))
    else:
        print("Total gain : {}{} €{}".format(Back.RED+Fore.WHITE, round(total_gain, 2), Style.RESET_ALL))
    time.sleep(30)
