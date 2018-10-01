"""

this fiel loads fast the 5y stocks data
"""

from multiprocessing import Pool
import requests as rq
import pandas as pd
import numpy as np
import json
import os
from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw


def get_list():
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
def get_stream(s):
    resp = rq.get('https://finviz.com/chart.ashx?t='+s+'&s=m&ty=c&ta=1', stream=True)
    return resp

def save_resp(resp, file_name):
    if (resp.headers['Content-Type'] == 'image/gif') & ('Content-Length' in resp.headers) & ('Last-Modified' in resp.headers):
        if (resp.headers['Last-Modified'] ==  'Thu, 15 Sep 2016 23:09:22 GMT') & (resp.headers['Content-Length'] == '2308'):
            open(file_name, 'a').close()
            return
    with open(file_name, 'wb') as fd:
        for chunk in resp.iter_content(2000):
            fd.write(chunk)
def resize(path, to_path):
    Image.open(path).resize((138,69), resample=Image.ANTIALIAS).convert('L').save(to_path)
def get_data(symbol):
    s = symbol
    symbol = symbol.replace('#','_')
    dr = os.path.join('charts',symbol[0])
    dr_small = os.path.join('charts_mid',symbol[0])
    if not os.path.exists(dr):
        os.mkdir(dr)
    if not os.path.exists(dr_small):
        os.mkdir(dr_small)
    path = os.path.join(dr, symbol+'.png')
    path_small = os.path.join(dr_small, symbol+'.png')
    if os.path.exists(path) and os.stat(path).st_size > 0 and os.path.exists(path_small):
        return
    try:
        print(symbol)
        if not os.path.exists(path):
            resp = get_stream(symbol)
            save_resp(resp, path)
#        if not os.path.exists(path_small):
        resize(path, path_small)
    except Exception as ex:
        print(ex)
        pass

def load_symbol(s):
    get_data(s['symbol'])

if __name__ == '__main__':
    p = Pool(20)
    p.map(load_symbol, get_list())
    
    
