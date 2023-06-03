import tushare as ts
from matplotlib import pyplot as plt

ts.set_token('2b33503f5c25fd8ddd78d2cc85827b7e6c8751dc9072bde2ab109214')
pro = ts.pro_api()

# df = pro.fund_daily(ts_code='513100.SH',start_date='20220101', end_date='20220315')['trade_date']
# print(df)
# print(pro.fund_adj(ts_code='513100.SH',start_date='20220101', end_date='20220315')['trade_date'])

def get_bar(fund,start_date,end_date):
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    final_close_data = []
    final_factors = []
    trade_dates_price = []
    trade_dates_factors = []
    if start_year==end_year:
        df = pro.fund_daily(ts_code=fund,start_date=start_date, end_date=end_date)
        close_data = list(df['close'])
        factors = list(pro.fund_adj(ts_code=fund, start_date=start_date, end_date=end_date)['adj_factor'])
        trade_dates_price =  list(pro.fund_daily(ts_code=fund,start_date=start_date, end_date=end_date)['trade_date']) + trade_dates_price
        trade_dates_factors =  list(pro.fund_adj(ts_code=fund,start_date=start_date, end_date=end_date)['trade_date']) + trade_dates_factors
        final_close_data = close_data + final_close_data
        final_factors = factors+ final_factors
    else:
        year_ = start_year
        while year_<=end_year:
            if year_==start_year:
                s_date = str(year_)+start_date[4:]
                e_date = str(year_)+'1231'
            elif year_==end_year:
                s_date = str(year_)+'0101'
                e_date = str(year_)+end_date[4:]
            else:
                s_date = str(year_) + '0101'
                e_date = str(year_) + '1231'
            close_data = list(pro.fund_daily(ts_code=fund, start_date=s_date, end_date=e_date)['close'])
            factors = list(pro.fund_adj(ts_code=fund, start_date=s_date, end_date=e_date)['adj_factor'])
            trade_dates_price =  list(
                pro.fund_daily(ts_code=fund, start_date=s_date, end_date=e_date)['trade_date']) + trade_dates_price
            trade_dates_factors = list(
                pro.fund_adj(ts_code=fund, start_date=s_date, end_date=e_date)['trade_date']) + trade_dates_factors
            final_close_data = close_data +final_close_data
            final_factors = factors+ final_factors
            year_ = year_+1
    final_close_data.reverse()
    final_factors.reverse()
    trade_dates_price.reverse()
    trade_dates_factors.reverse()
    new_values = dict()
    price_dic = dict()
    factor_dic = dict()
    for i in range(len(trade_dates_price)):
        price_dic[trade_dates_price[i]] = final_close_data[i]
    for i in range(len(trade_dates_factors)):
        factor_dic[trade_dates_factors[i]] = final_factors[i]
    dates_vec = list(pro.query('trade_cal', start_date=start_date, end_date=end_date)['cal_date'])
    opens = list(pro.query('trade_cal', start_date=start_date, end_date=end_date)['is_open'])
    dates = dict()
    # print(factor_dic)
    for i in range(len(dates_vec)):
        dates[dates_vec[i]] = opens[i]
    pre_price = 0
    for date in dates:
        if dates[date]==0:
            continue
        if date in price_dic and date in factor_dic:
            new_values[date] = price_dic[date]*factor_dic[date]/final_factors[-1]
            pre_price = new_values[date]
        else:
            new_values[date] = pre_price
    # print(new_values)
    # p = []
    # for key in new_values:
    #     p.append(new_values[key])
    # plt.plot(p)
    # plt.show()
    return new_values

    # for i in range(len(trade_dates_factors)):
    #     if trade_dates_factors[i]!=trade_dates_price[i]:
    #         print(trade_dates_factors[i],trade_dates_price[i])
    #         trade_dates_price = trade_dates_price[:i] +[trade_dates_factors[i]] +trade_dates_price[i:]
    #         final_close_data = final_close_data[:i]+[final_close_data[i-1]] + final_close_data[i:]
    #
    # if len(final_close_data)!=len(final_factors):
    #     print('error lengh is not equal')
    # else:
    #     for i in range(len(final_close_data)):
    #         new_values.append(final_close_data[i]*final_factors[i])
    # print(new_values)
    #
    # print(trade_dates_price)
    # print(trade_dates_factors)
    # print(final_close_data)
    # print(final_factors)

print(get_bar('513100.SH','200101','20220320'))

# fund = '513100.SH'
#
# ts.set_token('2b33503f5c25fd8ddd78d2cc85827b7e6c8751dc9072bde2ab109214')
# pro = ts.pro_api()
#
# df = pro.fund_daily(ts_code=fund,start_date='20140101', end_date='20180315')
# print(df)
#
# close_data = list(df['close'])
# close_data.reverse()
# print(close_data)
# factors = list(pro.fund_adj(ts_code=fund,start_date='20160101', end_date='20220315')['adj_factor'])
# factors.reverse()
# print(factors)
# adj_close_data = []
# print(len(close_data),len(factors))
# for i in range(len(close_data)):
#     adj_close_data.append(close_data[i]*factors[i])
#
#
# print(adj_close_data)