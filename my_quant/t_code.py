import tushare as ts
import pandas as pd
from datetime import datetime
import math
import json
import tqdm
from matplotlib import pyplot as plt


from functions.basic_functions import *

ts.set_token('1683668800a1289c82d373871e972a4a18fc5913247bf5c0819272d1')
pro = ts.pro_api()




#
# print(is_getting_better('300750.SZ', '20221230'))

# stock_list = get_stock_list('20221230')
# with open('D:/pythonProject/Quant/my_quant/stock_list.json', 'w') as f:
#     json.dump(stock_list, f)


# #
# # print(stock_list_ld)
# # stock_list_ld = ['300750.SZ', '000002.SZ', '000001.SZ', '000005.SZ']
# #
# df = pd.DataFrame()
# for stock in tqdm.tqdm(stock_list_ld):
#     succ, cur_df = get_finance_data(stock, '20221230')
#     if not succ:
#         continue
#     df = pd.concat([df, cur_df])
#
#
# df.to_csv('D:/pythonProject/Quant/my_quant/stock_data.csv', index=False)
# df = pd.read_csv('D:/pythonProject/Quant/my_quant/stock_data.csv')


# filted_stock = ffscore_stock(df, 6, stock_list_ld, '20221230')
# print(filted_stock)
# print(len(filted_stock))

# df = pro.daily_basic(ts_code='', trade_date='20221230', fields='ts_code,trade_date,pe,pb,close')
# df = df[df['pe'] > 0]
# df = df[df['pb'] > 0]
# new_code_list = []
# trade_information = pro.stk_limit(trade_date='20221230')
# close_value = list(df[df['ts_code'] == '300750.SZ']['close'])[0]
# print(close_value)
# print(is_not_up_down_limit('300750.SZ', close_value, trade_information))

#
# print(get_finance_data('000005.SZ', '20221230'))

#
# print(is_st_bj('002470.SZ', '20191028'))

with open('D:/pythonProject/Quant/my_quant/stock_list.json', 'r') as f:
    stock_list_ld = json.load(f)
stock_list_ld = stock_list_ld[:int(len(stock_list_ld)*0.05)]
vol_sum_list = []
close_price_list = []
increase_rate_list = []
# stock_list_ld = ['000005.SZ', '300750.SZ', '000001.SZ']
rank_stock_list = pd.DataFrame(stock_list_ld)
rank_stock_list.rename(columns={0: 'code'}, inplace=True)  # 重命名列名
circulating_market_cap_list = []
market_cap_list = []
for stock in tqdm.tqdm(rank_stock_list['code']):
    vol_sum, close_price, increase_rate, cir_market_cap, market_cap = get_vol_close_increase(stock, '20221230')
    circulating_market_cap_list.append(cir_market_cap)
    market_cap_list.append(market_cap)
    vol_sum_list.append(vol_sum)
    close_price_list.append(close_price)
    increase_rate_list.append(increase_rate)
rank_stock_list['circulating_market_cap'] = circulating_market_cap_list
rank_stock_list['market_cap'] = market_cap_list


min_price = min(close_price_list)
min_increase_period = min(increase_rate_list)
min_volume = min(vol_sum_list)
min_circulating_market_cap = min(rank_stock_list['circulating_market_cap'])
min_market_cap = min(rank_stock_list['market_cap'])
# 计算评分

totalcount = [[i,
               math.log(min_price / close_price_list[i]) * 2 +
               math.log(min_volume / vol_sum_list[i]) * 1 +
               math.log(min_increase_period / increase_rate_list[i]) * 1 +
               math.log(min_circulating_market_cap / rank_stock_list['circulating_market_cap'][i]) * 4 +
               math.log(min_market_cap / rank_stock_list['market_cap'][i]) * 4
               ] for i in rank_stock_list.index]

print(totalcount)

# 根据评分排序
totalcount.sort(key=lambda x: x[1])
# 选取排名靠前的股票
# 保留最多g.sellrank设置的个数股票代码返回
final_list = [rank_stock_list['code'][totalcount[-1 - i][0]] for i in range(min(8, len(rank_stock_list)))]
stock_list = final_list

print(totalcount)
print(stock_list)








