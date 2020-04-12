
# The Yahoo Finance financial page has changed so the current method of scraping that page no longer works.

# This was my first ever Python project so there are a few weaknesses.
# I was semi-experienced when this was written.

import requests
import re
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import statistics as st
import math as m


# Gather stock quotes
# Need to manually edit range to pages on gurufocus
def gather_quotes():

    # Currently set to flip through 3 pages
    # Also can set how many quotes on page. Currently 10
    for N in range(3):
        url = r"https://www.gurufocus.com/stock_list.php?m_country[]=USA&p=" + str(N) + r"&n=10" # n=10 = 10 quotes
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, timeout=5, headers=headers)
        except:
            print('Could not load URL on: ', str(N))
            continue

        status = response.status_code

        p = 0
        for n in range(2):
            if n == 1:
                print('Could not load page for: ', url)
                p = p + 1
                break
            if status != 200:
                response = requests.get(url, timeout=10)
                status = response.status_code
            else:
                break

        if p > 0:
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        table = soup.find('table', id="R1")
        tb = table.find('tbody')
        tr = tb.find_all('tr')

        for i in tr:
            td2 = i.select("td")[2].text
            price = re.findall(r"\d?\d?\d?\d?\d\.\d\d", td2)
            price = ''.join(price)
            price = float(price)
            if price >= 5 and price <= 400:
                td = i.select("td")[0]
                quote = td.find('a').text
                quotes.append(quote)

    table = {
        'Quotes': quotes
    }
    df = pd.DataFrame(table)
    df.to_csv(quote_collection, sep='|',
              index=False)

# Any quotes that don't have data on Yahoo are filtered out
def filter_fakes():

    quotes = pd.read_csv(quote_collection)
    quotes = quotes['Quotes'].tolist()

    for i in quotes:

        url = r'https://finance.yahoo.com/quote/' + str(i) + r'?p=' + (i)
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, timeout=5, headers=headers)
            status = response.status_code
        except:
            print('Could not find Filter Fake for: ' + str(i))
            quotes.remove(i)
            continue

        if status != 200:
            print('Could not find Filter Fake for: ' + str(i))
            quotes.remove(i)
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        no_results_lower_case = soup.find(string="No results for '" + i.lower() + "'")
        if no_results_lower_case is not None:
            quotes.remove(i)
            print('No results on Filter Fakes for: ' + str(i))
            continue

        p = 0
        check_results = []

        try:
            tbody = soup.select('tbody')[0]
        except:
            p = p + 1
        try:
            check_results.append(tbody.select('tr')[0].select('td')[1].find('span').get_text())
        except:
            p = p + 1
        try:
            check_results.append(tbody.select('tr')[1].select('td')[1].find('span').get_text())
        except:
            p = p + 1
        try:
            check_results.append(tbody.select('tr')[7].select('td')[1].find('span').get_text())
        except:
            p = p + 1

        try:
            tbody = soup.select('tbody')[1]
        except:
            p = p + 1
        try:
            check_results.append(tbody.select('tr')[0].select('td')[1].find('span').get_text())
        except:
            p = p + 1

        for ii in check_results:
            if ii == 'N/A':
                p = p + 1
                break

        if p > 0:
            quotes.remove(i)
            print('Fake Found for: ' + str(i))
            continue

    table = {
        'Quotes': quotes
    }
    df = pd.DataFrame(table)
    df.to_csv(quote_collection, sep='|',
              index=False)

# Get price history from Yahoo
def list_making():
    global quote_list
    global day_list
    global open_list
    global low_list
    global high_list
    global close_list
    global volume_list

    quotes = pd.read_csv(quote_collection)
    quotes = quotes['Quotes'].tolist()

    for i in quotes:

        url = r'https://finance.yahoo.com/quote/' + i + '/history'
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, timeout=5, headers=headers)
        except:
            print('could not find: ', url)
            continue

        status = response.status_code

        p = 0
        for n in range(2):
            if n == 1:
                print('Could not load price history page for: ', i, ', ', url)
                quotes.remove(i)
                p = p + 1
                break
            if status != 200:
                response = requests.get(url, timeout=10)
                status = response.status_code
            else:
                break

        if p > 0:
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        no_results_lower_case = soup.find(string="No results for '" + i.lower() + "'")
        if no_results_lower_case is not None:
            continue

        tbody = soup.find('tbody')
        rows = tbody.find_all('tr')

        if len(rows) < 100:
            print('rows less than 100 for: ' + i)
            continue

        new = 0
        for ii in rows:
            td = ii.find_all('td')
            if new != 0:
                break
            for iii in td:
                test = iii.find('span')
                if test is None:
                    new = new + 1

        if new != 0:
            continue

        open_list_temp = []
        low_list_temp = []
        high_list_temp = []
        close_list_temp = []
        volume_list_temp = []

        td = datetime.date.today()

        # delta counts weekends. In 90 days there are 18 5-day weeks
        # for each week 2 days are added to total days
        # so to get 90 days of trading go 90 days and then over for every weekend day (18*2 = 36)
        # then closer to getting 90 trading days
        # (could have just looped over 90 days)
        # round up to 140 for extra. Going to chop all down to 90 data entries.
        # should have just looped over 90 rows but at least I got experience with dates

        tdelta = datetime.timedelta(days=140)
        td_minus = td - tdelta

        n = 0

        for ii in rows:

            n = n + 1

            date = ii.select("td")[0].find("span").get_text()
            date = datetime.datetime.strptime(date, '%b %d, %Y')
            date = date.date()

            if date >= td_minus:

                open = ii.select("td")[1].find("span").get_text()
                if open == 'Dividend' or open == 'Stock Split':
                    continue
                open = re.findall(r"\d?\d?\d?\d\.\d\d", open)
                open = ''.join(open)
                open = float(open)

                high = ii.select("td")[2].find("span").get_text()
                high = re.findall(r"\d?\d?\d?\d\.\d\d", high)
                high = ''.join(high)
                high = float(high)

                low = ii.select("td")[3].find("span").get_text()
                low = re.findall(r"\d?\d?\d?\d\.\d\d", low)
                low = ''.join(low)
                low = float(low)

                close = ii.select("td")[5].find("span").get_text()
                close = re.findall(r"\d?\d?\d?\d\.\d\d", close)
                close = ''.join(close)
                close = float(close)

                volume = ii.select("td")[6].find("span").get_text()
                volume = re.findall(r"\d", volume)
                volume = ''.join(volume)
                volume = float(volume)

                day_list.append(n)
                quote_list.append(i)
                open_list_temp.append(open)
                low_list_temp.append(low)
                high_list_temp.append(high)
                close_list_temp.append(close)
                volume_list_temp.append(volume)

        open_list_temp.reverse()
        low_list_temp.reverse()
        high_list_temp.reverse()
        close_list_temp.reverse()
        volume_list_temp.reverse()

        open_list = open_list + open_list_temp
        low_list = low_list + low_list_temp
        high_list = high_list + high_list_temp
        close_list = close_list + close_list_temp
        volume_list = volume_list + volume_list_temp

# Create pandas data frame
def data_frame():
    global df

    Data_Table = {
        'Quotes': quote_list,
        'Day': day_list,
        'Open': open_list,
        'Low': low_list,
        'High': high_list,
        'Close': close_list,
        'Volume': volume_list
    }

    df = pd.DataFrame(Data_Table)
    df.to_csv(all_quotes_price_data, sep='|', index=False)

# Extract unique companies from master list.
# Create list of unique data frames
def grouping():
    global dfL
    global temp_quotes
    global group

    table = pd.read_csv(all_quotes_price_data, sep='|')
    df = pd.DataFrame(table)
    quote_list = df['Quotes'].tolist()

    temp_quotes = list(dict.fromkeys(quote_list))

    group = df.groupby('Quotes')

    for i in temp_quotes:
        frame = group.get_group(i)
        frame = frame.reset_index()
        frame = frame.truncate(after=89)
        dfL.append(frame)

# Get Z score of volume and filter based on score
def Z_Volume():
    global sd_volumes
    global vol_mean

    x_volumes = []
    x_devs2 = []

    for i in range(len(dfL)):
        x_volumes.append(dfL[i]['Volume'].mean())

    vol_mean = sum(x_volumes) / len(dfL)

    for i in range(len(dfL)):
        x_devs2.append((dfL[i]['Volume'].mean() - vol_mean) ** 2)

    sd_volumes = (sum(x_devs2)) / len(dfL)

    for i in temp_quotes:
        Z_score = (group.get_group(i)['Volume'].mean() - vol_mean) / sd_volumes

        if Z_score <= -2:
            temp_quotes.remove(i)

# Get linear regression slope
def regression():
    global dfL2
    global SLOPE
    global SLOPES
    global df2

    for i in temp_quotes:
        try:
            stakhanov = group.get_group(i)
            stakhanov = stakhanov.reset_index(drop=True)
            top = len(stakhanov['Close'])

            x_values = []
            for ii in range(top):
                x_values.append(ii)

            x_mean = st.mean(x_values)

            y_values = []
            for ii in range(top):
                y_values.append(stakhanov['Close'][ii])

            y_values = [float(ii) for ii in y_values]

            y_mean = st.mean(y_values)

            xmmx = []
            for ii in range(top):
                xmmx.append(x_values[ii] - x_mean)

            Sxmmx = sum(xmmx)

            ymmy = []
            for ii in range(top):
                ymmy.append(y_values[ii] - y_mean)

            Symmy = sum(ymmy)

            xmmxtymmy = []
            for ii in range(top):
                xmmxtymmy.append(xmmx[ii] * ymmy[ii])
            Sxmmxtymmy = sum(xmmxtymmy)

            xmmx2 = []
            for ii in range(top):
                xmmx2.append((x_values[ii] - x_mean) ** 2)
            Sxmmx2 = sum(xmmx2)

            ymmy2 = []
            for ii in range(top):
                ymmy2.append((y_values[ii] - y_mean) ** 2)
            Symmy2 = sum(ymmy2)

            covxy = Sxmmxtymmy / top

            sdX = m.sqrt(Sxmmx2 / top)
            sdY = m.sqrt(Symmy2 / top)

            r = covxy / (sdX * sdY)

            r2 = r ** 2

            slope = Sxmmxtymmy / Sxmmx2

            # r squared is a max of one and min of negative infinity
            # so multiplying regression slope will discount
            slope = slope * r2

            SLOPE = slope
            SLOPES.append(SLOPE)

            # b = y_mean - (slope * x_mean)

            # Could use below to predict future with regression
            # pred = []
            # for ii in range(top, top + 30):
            #     reg_y = slope * ii + b
            #     pred.append(reg_y)

        except:
            SLOPE = 0
            SLOPES.append(SLOPE)

# Get modified average revenue change
def rev_avrg(Q):
    global rev_
    global zipped

    zipped = zip(temp_quotes, SLOPES)
    zipped = list(zipped)

    x = 0
    for i in Q:

        url = r"https://finance.yahoo.com/quote/" + i + "/financials?p=" + i
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            response = requests.get(url, timeout=5, headers=headers)
        except:
            print('could not find: ', url)
            zipped.remove(zipped[x])
            continue

        status = response.status_code

        if status != 200:
            zipped.remove(zipped[x])
            print('Could not load revenue page for: ', i, ', ', url)
            continue

        try:
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find('table')
            table = table.find('tbody')
            rows = table.find_all('tr')
            rev = rows[1]
            rev = rev.find_all('td')
        except:
            zipped.remove(zipped[x])
            continue

        n = 0
        revs = []
        for ii in range(1, 5):
            try:
                temp = rev[ii]
            except:
                n = n + 1
                continue

            if rev[ii].find('span') is not None:
                rev2 = rev[ii].find('span').get_text()
                rev2 = re.findall(r"\d", rev2)
                rev2 = ''.join(rev2)
                try:
                    p = 0
                    rev2 = int(rev2)
                    revs.append(rev2)
                except:
                    p = p + 1
                    print('Could not turn revenue to int for ' + i)
                    break
            else:
                n = n + 1

        if p != 0:
            zipped.remove(zipped[x])
            continue

        revs.reverse()

        chg1 = []
        fail = 0

        if n == 0:
            for ii in range(len(revs)):
                if ii == len(revs) - 1:
                    break
                result = (revs[ii + 1] - revs[ii]) / revs[ii]
                if result < -.5:
                    result = 0
                    chg1.append(result)
                    fail = fail + 1
                if result > 2:
                    result = 2
                    chg1.append(result)
                    fail = fail + 0
                if result > -.5 and result < 2:
                    chg1.append(result)
                    fail = fail + 0
            if fail > 0:
                chg2 = 0
            else:
                chg2 = sum(chg1) / (len(revs))
            if chg2 > 0:
                chg2 = chg2 * 1
            else:
                chg2 = chg2 * 1

        if n == 1:
            for ii in range(len(revs)):
                if ii == len(revs) - 1:
                    break
                result = (revs[ii + 1] - revs[ii]) / revs[ii]
                if result < -.5:
                    result = 0
                    chg1.append(result)
                    fail = fail + 1
                if result > 2:
                    result = 2
                    chg1.append(result)
                    fail = fail + 0
                if result > -.5 and result < 2:
                    chg1.append(result)
                    fail = fail + 0
            if fail > 0:
                chg2 = 0
            else:
                chg2 = sum(chg1) / (len(revs))
            if chg2 > 0:
                chg2 = chg2 * .8
            else:
                chg2 = chg2 * 1.2

        if n == 2:
            for ii in range(len(revs)):
                if ii == len(revs) - 1:
                    break
                result = (revs[ii + 1] - revs[ii]) / revs[ii]
                if result < -.5:
                    result = 0
                    chg1.append(result)
                    fail = fail + 1
                if result > 2:
                    result = 2
                    chg1.append(result)
                    fail = fail + 0
                if result > -.5 and result < 2:
                    chg1.append(result)
                    fail = fail + 0
            if fail > 0:
                chg2 = 0
            else:
                chg2 = sum(chg1) / (len(revs))
            if chg2 > 0:
                chg2 = chg2 * .6
            else:
                chg2 = chg2 * 1.4

        if n == 3:
            cg2 = 0

        if n == 4:
            cg2 = 0

        rev_.append(chg2)

        x = x + 1

# Return final list of scores
def finish():
    temp_quotes, SLOPES = zip(*zipped)

    temp_quotes = list(temp_quotes)
    SLOPES = list(SLOPES)

    SLOPES2 = [round(a, 5) for a in SLOPES]

    rev_2 = [round(a, 5) for a in rev_]

    table_2 = {
        'Stock': temp_quotes,
        'Slopes': SLOPES2,
        'Rev Change': rev_2
    }

    df2 = pd.DataFrame(table_2)

    df2.to_csv(all_quotes_price_data, sep='|',
               index=False)

    score = []

    for i in range(len(temp_quotes)):
        score.append(((SLOPES[i] * .85) + (rev_[i] * .15)) / 2)

    score2 = [round(a, 5) for a in score]

    table_3 = {
        'Stock': temp_quotes,
        'Score': score
    }

    df3 = pd.DataFrame(table_3)

    # df3 = df3.nlargest(20, 'Score')

    df3.to_csv(list_of_scores, sep='|', index=False)

    print(df3)

quotes = []
quote_list = []
day_list = []
open_list = []
low_list = []
high_list = []
close_list = []
volume_list = []
rev_ = []
dfL = []
dfL2 = []
pred = []
SLOPES = []
Zscores = []

# Main:
# ==========

quote_collection = input('Enter CSV file and path for list of quotes: ')
all_quotes_price_data = input('Enter CSV file and path for quotes and prices: ')
list_of_scores = input('Enter CSV file and path for list of scores: ')

try:
    gather_quotes()
    filter_fakes()
    list_making()
    data_frame()
    grouping()
    Z_Volume()
    regression()
    rev_avrg(temp_quotes)
    finish()
except:
    print('Failure')
    exit()
