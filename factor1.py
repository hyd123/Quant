import pandas as pd
import numpy as np
import tushare as ts
import alphalens
ts.set_token('1683668800a1289c82d373871e972a4a18fc5913247bf5c0819272d1')
pro = ts.pro_api()
wdays = pro.trade_cal(exchange_id='', start_date='20180101', end_date='20180131')
wdays = wdays[wdays.is_open==1].cal_date.values.tolist()
factors_list = []

print(wdays)

for idate in wdays:
    temp_df = pro.query('daily_basic', ts_code='', trade_date=idate)
    factors_list.append(temp_df)
    print(temp_df)
factor_df = pd.concat(factors_list)
print(factor_df)

factor = factor_df.loc[:,['ts_code','trade_date','ps_ttm']].set_index(['trade_date','ts_code'])
factor = factor.unstack().fillna(method='ffill').stack()
print(factor)

def get_bar(iticker):
    temp_quote = ts.pro_bar(ts_code=iticker, start_date='2018-01-01', end_date='2018-01-31', adj='qfq').loc[:, ['trade_date', 'close']]
    temp_quote['ts_code'] = iticker
    return temp_quote


quote_list = []
tickers = list(set(factor_df.ts_code))

print(len(tickers))


for i, ticker in enumerate(tickers):
    print(ticker)
    print(i)
    res = get_bar(ticker)
    quote_list.append(res)
quotes = pd.concat(quote_list)
prices = quotes.pivot(index='trade_date',columns='ts_code',values='close')
print(prices)



# from multiprocessing import Pool
# pool = Pool(1)
# res = pool.map(worker,tickers)
# quotes = pd.concat(res)
#
# quotes.rename(columns={'date':'trade_date'},inplace=True)
#
# factor_df.trade_date = pd.to_datetime(factor_df.trade_date.astype('str'))
# quotes.trade_date = pd.to_datetime(quotes.trade_date)
#
factor = factor_df.loc[:,['ts_code','trade_date','ps_ttm']].set_index(['trade_date','ts_code'])
factor = factor.unstack().fillna(method='ffill').stack()

prices = quotes.pivot(index='trade_date',columns='ts_code',values='close')

factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
    factor,
    prices,
    groupby=None,
    quantiles=5,
    periods=(10,20,40),
    filter_zscore=None)

mean_return_by_q_daily, std_err = alphalens.performance.mean_return_by_quantile(factor_data, by_date=True)
mean_return_by_q, std_err_by_q = alphalens.performance.mean_return_by_quantile(factor_data, by_date=False)

alphalens.plotting.plot_quantile_returns_bar(mean_return_by_q)

alphalens.plotting.plot_quantile_returns_violin(mean_return_by_q_daily)

quant_return_spread, std_err_spread = alphalens.performance.compute_mean_returns_spread(mean_return_by_q_daily,
                                                                                        upper_quant=5,
                                                                                        lower_quant=1,
                                                                                        std_err=std_err)

alphalens.plotting.plot_mean_quantile_returns_spread_time_series(quant_return_spread, std_err_spread)
