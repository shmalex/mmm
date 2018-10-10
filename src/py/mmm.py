import requests as rq
import pandas as pd
from scipy.optimize import minimize
from scipy.misc import factorial
import matplotlib.pyplot as plt
import numpy as np

from collections import Counter

from bokeh.plotting import figure, ColumnDataSource, output_file, show
from bokeh.io import output_notebook, show
from bokeh.models import HoverTool
from sklearn.preprocessing import StandardScaler
from MulticoreTSNE import MulticoreTSNE as TSNE
import json
import os
import glob

def count_probs(sr):
    growl = []
    max_logs = []
    pr = 1
    cnt = 0
    for i, v in enumerate(sr):
        if pr == v:
            if v == True:
                cnt = cnt +1
                growl.append(cnt)
        else:
            if (cnt > 0):
                max_logs.append(cnt)
            pr = v
            cnt = 0
            growl.append(0)
          
    data = np.array(list(Counter(max_logs).items()))
    if (len(data) == 0):
        return
    total_events = (data[:,0]*data[:,1]).sum()
    pro_groups = dict(Counter(max_logs))
    ret = {}
    for pg_key in sorted(pro_groups.keys()):
        ret[pg_key] = pg_key*pro_groups[pg_key] / total_events
    return list(ret.values())

def count_logs(dt):
    """
    return the counters and logs array
    """
    growl = []
    max_logs = []
    pr = True
    cnt = 0
    for i, v in enumerate(dt):
        if pr == v:
            if v == True:
                cnt = cnt +1
                growl.append(cnt)
        else:
            if (cnt > 0):
                max_logs.append(cnt)
            pr = v
            cnt = 0
            growl.append(0)
    return Counter(max_logs), max_logs

def count_logs_fixed(dt, max_logs=5):
    """returns fixed numbers of logs"""
    ret = count_logs(dt)
    return [ret[i+1] for i in range(max_logs)]

def get_last_n(df, n_days):
    """
    return n last days in daya frames
    """
    return df.iloc[:n_days]

def get_last_behind_n(df, n_days):
    """
    returns first n_days from data frames
    """
    return df.iloc[n_days:]

def get_symbols_list():
    """
    return the list of symbols
    """
    if os.path.exists('symbols.json'):
        with open('symbols.json',mode='r') as f:
            return json.load(f)
    try:
        data = rq.get('https://api.iextrading.com/1.0/ref-data/symbols').json()
        with open('symbols.json',mode='w') as f:
            json.dump(data, f)
        return data
    except Exception as ex:
        print(ex)
        pass

def get_stats(symbol):
    """
    returns the stats of change percent
    """
    try:
        path = get_path(symbol.upper())
        with open(path, mode='r') as f:
            ret = json.load(f)
            return (ret["year5ChangePercent"],
        ret["year2ChangePercent"],
        ret["year1ChangePercent"],
        ret["ytdChangePercent"],
        ret["month6ChangePercent"],
        ret["month3ChangePercent"],
        ret["month1ChangePercent"],
        ret["day5ChangePercent"],
        ret["day30ChangePercent"])
    except Exception as ex:
        print(ex)
        return 0,0,0,0,0,0,0,0,0

    
def get_path(symbol):
    """ 
    returns path to symbols
    """
    return os.path.join('stats',symbol[0], symbol+'.json')

def get_datas():
    """
    yields the stocks data
    """
    for ls in get_list(get_stocks_type()):
            yield get_data(ls[0])

def get_list(stock_type, p = 'stocks'):
    """
    yields the list tuple of symbol, data for stocks
    """
    for path in glob.iglob(p+'/**/**'):
        s = os.path.basename(path).replace('.json','').upper()
        with open(path, mode='r') as f:
            data = json.load(f)
            if len(data) == 0 or s not in stock_type:
                continue
            yield (s, data)

def get_data(symbol):
    """ 
    returns the pairs (symbol, object) stocks data from file
    """
    dr = os.path.join('stocks',symbol[0])
    if not os.path.exists(dr):
        os.mkdir(dr)
    path = os.path.join(dr, symbol+'.json')
    if os.path.exists(path) and os.stat(path).st_size > 0:
        with open(path, mode='r') as f:
            return (symbol, json.load(f))
    try:
        print(symbol)
        data = rq.get('https://api.iextrading.com/1.0/stock/'+symbol+'/chart/5y').json()
        with open(path,mode='w') as f:
            json.dump(data, f)
        return (symbol,data)
    except Exception as ex:
        print(ex)
        pass

def get_last_n(d, n_days):
    return d.iloc[:n_days]

def get_stocks_type():
    """ return stocks of dict filtering the et, ce, N/A """
    stock_type = {}
    for s in get_symbols_list():
        if s['type'] == 'et' or s['type'] == 'ce' or s['type'] == 'N/A':
            continue
        stock_type[s['symbol']] = s['type']
    return stock_type

def get_events(stock, col='0.01', limit=0.01):
    d = get_data(stock)
    df = pd.DataFrame(data=get_data(stock)[1])
    df.head()
    df['grow'] =  (df['high'] - df['open'])/df['open']
    df[col] = df['grow']>=limit
    return np.flip(np.array(df[col]),0)


def show_poisson(stock):
    """ returns the fitter poisson values """
    d = get_data(stock)
    df = pd.DataFrame(data=get_data(stock)[1])
    df.head()
    df['grow'] =  (df['high'] - df['open'])/df['open']
    df['0.01'] = df['grow']>=0.01
    counter, data = count_logs(df['0.01'])
    return fit_poisson(data)

def fit_poisson(data, show_chart=False):
    def poisson(k, lamb):
        """poisson pdf, parameter lamb is the fit parameter"""
        return (lamb**k/factorial(k)) * np.exp(-lamb)


    def negLogLikelihood(params, data):
        """ the negative log-Likelohood-Function"""
        lnl = - np.sum(np.log(poisson(data, params[0])))
        return lnl


    # get poisson deviated random numbers
    #data = np.random.poisson(2, 1000)

    
    # minimize the negative log-Likelihood

    result = minimize(negLogLikelihood,  # function to minimize
                      x0=np.ones(1),     # start value
                      args=(data,),      # additional arguments for function
                      method='Powell',   # minimization method, see docs
                      )
    if not show_chart:
        return result.x
    # result is a scipy optimize result object, the fit parameters 
    # are stored in result.x
    #print(result)

    # plot poisson-deviation with fitted parameter
    x_plot = np.linspace(0, 20, 1000)

    plt.hist(data, bins=np.arange(15) - 0.5, normed=True)
    plt.plot(x_plot, poisson(x_plot, result.x), 'r-', lw=2)
    plt.show()
    return result.x