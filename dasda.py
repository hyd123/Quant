# import jqdatasdk
# from jqdatasdk import *
# from jqdatasdk.alpha101 import *
# #获取聚宽因子库所有因子
# auth('18675544580', 'He7277320')
# a = alpha_001('20230424')
# print(a)
import json
import time
import os
import numpy as np
import pandas
import tushare as ts
import matplotlib.pyplot as plt
import tqdm
from alpha101.feature_generate import *

#设置token
ts.set_token('1683668800a1289c82d373871e972a4a18fc5913247bf5c0819272d1')
#初始pro对象
pro = ts.pro_api()

df = pro.daily(ts_code='000001.SZ', start_date='20170901', end_date='20180918')

print(df)

def vwap(df):
    """
    volume-weighted average price
    """
    return (df.volume * df.close) / df.volume

new_df = pandas.DataFrame()
new_df['open'] = df['open']
new_df['high'] = df['high']
new_df['low'] = df['low']
new_df['close'] = df['close']
new_df['volume'] = df['vol']
new_df['returns'] = df['pct_chg']
new_df['vwap'] = vwap(new_df)

data = np.array(get_all_factors(new_df).values)





