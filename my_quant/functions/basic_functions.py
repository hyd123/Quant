import copy

import tushare as ts
import pandas as pd
from datetime import datetime
import numpy as np
import math
import time
import tqdm
import functions.global_variables as gv
from datetime import datetime, timedelta


ts.set_token('c7469f373bc382729fcd19f4b014a58b5679bb0578c8ee9841aea01c')
pro = ts.pro_api()


def get_finance_data(ts_code, now_date_time):

    end_date_time = now_date_time + timedelta(days=-1)
    end_date = end_date_time.strftime('%Y%m%d')
    df = pro.fina_indicator_vip(ts_code=ts_code,
                                start_date=(end_date_time + timedelta(days=-365 * 2)).strftime('%Y%m%d'), end_date=end_date)
    information_list = ['ts_code', 'ann_date', 'end_date', 'profit_dedt']
    new_df = df[information_list].drop_duplicates(subset='end_date', keep='first', inplace=False).head(6)
    ba = pro.balancesheet(ts_code=ts_code, start_date=(end_date_time + timedelta(days=-365 * 2)).strftime('%Y%m%d'), end_date=end_date,
                          fields='ts_code,ann_date,end_date,total_cur_liab,total_ncl,total_assets,total_cur_assets').drop_duplicates(
        subset='end_date',
        keep='first', inplace=False).head(6)
    cash_list = ['ts_code', 'ann_date', 'end_date', 'n_cashflow_act']
    cash = pro.cashflow(ts_code=ts_code, start_date=(end_date_time + timedelta(days=-365 * 2)).strftime('%Y%m%d'), end_date=end_date)[
        cash_list].drop_duplicates(
        subset='end_date', keep='first', inplace=False).head(6)
    income = pro.income(ts_code=ts_code, start_date=(end_date_time + timedelta(days=-365 * 2)).strftime('%Y%m%d'), end_date=end_date,
                        fields='ts_code,ann_date,end_date,total_revenue,oper_cost').drop_duplicates(subset='end_date',
                                                                                                    keep='first',
                                                                                                    inplace=False).head(6)
    result = pd.merge(pd.merge(pd.merge(new_df, ba, on='end_date'),
                               cash, on='end_date'), income,
                      on='end_date')[['end_date', 'profit_dedt', 'n_cashflow_act',
                                      'total_cur_liab', 'total_ncl', 'total_assets', 'total_revenue', 'oper_cost',
                                      'total_cur_assets']]
    need_update_list = ['profit_dedt', 'n_cashflow_act', 'total_revenue', 'oper_cost']
    result = result.dropna()
    end_date_list = list(result['end_date'])
    for key in need_update_list:
        vals = list(result[key])
        for i in range(len(end_date_list) - 1):
            if not end_date_list[i].endswith('0331'):
                vals[i] = vals[i] - vals[i + 1]
        result[key] = vals
    result = result.head(5).dropna()
    if len(result) < 5:
        return False, None
    result['ts_code'] = [ts_code] * 5
    return True, result

def is_one_half_year(stock_code, target_date):
    data = pro.stock_basic(ts_code=stock_code, list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    if len(data) == 0:
        return False
    if (datetime.strptime(target_date, '%Y%m%d') + timedelta(days=-548)).strftime('%Y%m%d') > list(data['list_date'])[0]:
        return True
    return False


def is_not_st_bj(stock_code, target_date):
    if 'BJ' in stock_code:
        return False
    target_date = datetime.strptime(target_date, '%Y%m%d')
    df = pro.namechange(ts_code=stock_code, fields='ts_code,name,start_date,end_date,change_reason')
    df = df[df.name.str.contains('ST')]
    for i in range(len(df)):
        sds = df.iloc[i, 2]
        eds = df.iloc[i, 3]
        sd = datetime.strptime(sds, '%Y%m%d')
        if eds == None:
            ed = datetime.now()
        else:
            ed = datetime.strptime(eds, '%Y%m%d')
        if (target_date - sd).days >= 0 and (target_date - ed).days <= 0:
            return False
    return True


def is_getting_better(stock_code, target_date):
    df = pro.fina_indicator_vip(ts_code=stock_code, start_date=(datetime.strptime(target_date, '%Y%m%d') +
                                                                timedelta(days=-365 * 2)).strftime('%Y%m%d'), end_date=target_date)
    information_list = ['ts_code', 'ann_date', 'end_date', 'roe_dt', 'tr_yoy', 'netprofit_yoy']
    new_df = df[information_list].drop_duplicates(subset='end_date', keep='first', inplace=False).head(2).dropna()
    end_date_list = list(new_df['end_date'])
    vals = list(new_df['roe_dt'])
    for i in range(len(end_date_list) - 1):
        if not end_date_list[i].endswith('0331'):
            vals[i] = vals[i] - vals[i + 1]
    new_df['roe_dt'] = vals
    new_df = new_df.dropna()
    if len(new_df) <= 0:
        return False
    if new_df['roe_dt'].values[0] <= 0:
        return False
    if new_df['tr_yoy'].values[0] <= 0:
        return False
    if new_df['netprofit_yoy'].values[0] <= 0:
        return False
    return True


def is_not_up_down_limit(code, close_value, trade_information):
    trade_information_code = trade_information[trade_information['ts_code'] == code]
    if len(trade_information_code) != 1:
        return True
    if close_value >= list(trade_information_code['up_limit'])[0] or close_value <= \
            list(trade_information_code['down_limit'])[0]:
        return False
    return True


def get_stock_list(now_date_time):
    trade_date_pre1d = (now_date_time + timedelta(days=-1)).strftime('%Y%m%d')
    tem_cal = copy.deepcopy(gv.cal_date)
    if list(tem_cal[tem_cal['cal_date'] == trade_date_pre1d]['is_open'])[0] != 1:
        trade_date_pre1d = list(tem_cal[tem_cal['cal_date'] == trade_date_pre1d]['pretrade_date'])[0]
    df = pro.daily_basic(ts_code='', trade_date=trade_date_pre1d, fields='ts_code,trade_date,pe,pb,close')
    df = df[df['pe'] > 0]
    df = df[df['pb'] > 0]
    new_code_list = []
    trade_information = pro.stk_limit(trade_date=trade_date_pre1d)
    for code in list(df['ts_code']):
        close_value = list(df[df['ts_code'] == code]['close'])[0]
        condition_1 = is_not_st_bj(code, trade_date_pre1d)
        condition_2 = is_getting_better(code, trade_date_pre1d)
        condition_3 = is_not_up_down_limit(code, close_value, trade_information)
        condition_4 = is_one_half_year(code, trade_date_pre1d)
        if condition_1 and condition_2 and condition_3 and condition_4:
            new_code_list.append(code)
    return new_code_list


def ffscore_stock(h, score, security_list):
    def ttm_sum(x):
        return x.iloc[1:].sum()
    def ttm_avg(x):
        return x.iloc[1:].mean()
    def pre_ttm_sum(x):
        return x.iloc[:-1].sum()
    def pre_ttm_avg(x):
        return x.iloc[:-1].mean()
    def val_1(x):
        return x.iloc[-1]
    def val_2(x):
        if len(x.index) > 1:
            return x.iloc[-2]
        else:
            return np.NAN
    # 扣非利润
    adjusted_profit_ttm = h.groupby('ts_code')['profit_dedt'].apply(ttm_sum)
    adjusted_profit_ttm_pre = h.groupby('ts_code')['profit_dedt'].apply(pre_ttm_sum)
    # 总资产平均
    total_assets_avg = h.groupby('ts_code')['total_assets'].apply(ttm_avg)
    total_assets_avg_pre = h.groupby('ts_code')['total_assets'].apply(pre_ttm_avg)
    # 经营活动产生的现金流量净额
    net_operate_cash_flow_ttm = h.groupby('ts_code')['n_cashflow_act'].apply(ttm_sum)
    # 长期负债率: 长期负债/总资产
    long_term_debt_ratio = h.groupby('ts_code')['total_ncl'].apply(val_1) / h.groupby('ts_code')['total_assets'].apply(val_1)
    long_term_debt_ratio_pre = h.groupby('ts_code')['total_ncl'].apply(val_2) / h.groupby('ts_code')['total_assets'].apply(val_2)
    # 流动比率：流动资产/流动负债
    current_ratio = h.groupby('ts_code')['total_cur_assets'].apply(val_1) / h.groupby('ts_code')['total_cur_liab'].apply(val_1)
    current_ratio_pre = h.groupby('ts_code')['total_cur_assets'].apply(val_2) / h.groupby('ts_code')['total_cur_liab'].apply(val_2)
    # 营业收入
    operating_revenue_ttm = h.groupby('ts_code')['total_revenue'].apply(ttm_sum)
    operating_revenue_ttm_pre = h.groupby('ts_code')['total_revenue'].apply(pre_ttm_sum)
    # 营业成本
    operating_cost_ttm = h.groupby('ts_code')['oper_cost'].apply(ttm_sum)
    operating_cost_ttm_pre = h.groupby('ts_code')['oper_cost'].apply(pre_ttm_sum)
    # 1. ROA 资产收益率
    roa = adjusted_profit_ttm / total_assets_avg
    roa_pre = adjusted_profit_ttm_pre / total_assets_avg_pre
    # 2. OCFOA 经营活动产生的现金流量净额/总资产
    ocfoa = net_operate_cash_flow_ttm / total_assets_avg
    # 3. ROA_CHG 资产收益率变化
    roa_chg = roa - roa_pre
    # 4. OCFOA_ROA 应计收益率: 经营活动产生的现金流量净额/总资产 -资产收益率
    ocfoa_roa = ocfoa - roa
    # 5. LTDR_CHG 长期负债率变化 (长期负债率=长期负债/总资产)
    ltdr_chg = long_term_debt_ratio - long_term_debt_ratio_pre
    # 6. CR_CHG 流动比率变化 (流动比率=流动资产/流动负债)
    cr_chg = current_ratio - current_ratio_pre
    # 8. GPM_CHG 毛利率变化 (毛利率=1-营业成本/营业收入)
    gpm_chg = operating_cost_ttm_pre/operating_revenue_ttm_pre - operating_cost_ttm/operating_revenue_ttm
    # 9. TAT_CHG 资产周转率变化(资产周转率=营业收入/总资产)
    tat_chg = operating_revenue_ttm/total_assets_avg - operating_revenue_ttm_pre/total_assets_avg_pre
    # spo_list = list(set(finance.run_query(
    #     query(
    #         finance.STK_CAPITAL_CHANGE.code
    #     ).filter(
    #         finance.STK_CAPITAL_CHANGE.code.in_(security_list),
    #         finance.STK_CAPITAL_CHANGE.pub_date.between(one_year_ago, my_watch_date),
    #         finance.STK_CAPITAL_CHANGE.change_reason_id == 306004)
    # )['code']))
    # spo_score = pd.Series(True, index = security_list)
    # if spo_list:
    #     spo_score[spo_list] = False
    df_scores = pd.DataFrame(index=security_list)# 1
    df_scores['roa'] = (roa>0.0).astype(int) #赚钱能力强于国债# 2
    df_scores['ocfoa'] = (ocfoa>0).astype(int) # 3
    df_scores['roa_chg'] = (roa_chg>0).astype(int) # 4
    df_scores['ocfoa_roa'] = (ocfoa_roa>0).astype(int) # 5
    df_scores['ltdr_chg'] = (ltdr_chg<=0).astype(int) # 6
    df_scores['cr_chg'] = (cr_chg>0).astype(int) # 7
    # df_scores['spo'] = spo_score  > 0# 8
    df_scores['gpm_chg'] = (gpm_chg>0).astype(int) # 9
    df_scores['tat_chg'] = (tat_chg>0).astype(int) # 合计
    df_scores = df_scores.dropna()
    df_scores['total'] = df_scores['roa'] + df_scores['ocfoa'] + df_scores['roa_chg'] + \
        df_scores['ocfoa_roa'] + df_scores['ltdr_chg'] + df_scores['cr_chg'] + df_scores['gpm_chg'] + df_scores['tat_chg']
    res  = df_scores.loc[lambda df_scores: df_scores['total'] > score].sort_values(by = 'total',ascending=False).index
    return list(res)


def get_vol_close_increase(code, end_date_time):
    end_date = end_date_time.strftime('%Y%m%d')
    df = pro.daily(start_date=(end_date_time + timedelta(days=-100)).strftime('%Y%m%d'), end_date=end_date, ts_code=code)
    if len(df) == 0:
        return False, None, None, None, None, None
    vol_sum = df.head(5)['vol'].sum()
    close_price = list(df['close'])[0]
    pre_close_list = list(df.head(60)['pre_close'])
    pricenow = pre_close_list[0]
    price_period = pre_close_list[-1]
    if not math.isnan(pricenow) and not math.isnan(price_period) and price_period != 0:
        increase_rate = pricenow / price_period
    else:
        increase_rate = 100
    df2 = pro.daily_basic(start_date=(end_date_time + timedelta(days=-60)).strftime('%Y%m%d'), end_date=end_date, ts_code=code)
    cir_market_cap = df2['circ_mv'].head(1).sum()
    market_cap = df2['total_mv'].head(1).sum()
    return True, vol_sum, close_price, increase_rate, cir_market_cap, market_cap


def get_stock_rank_m_m(stock_list_ld, now_date):
    print('begin to rank_m_m')
    trade_date_pre1d = now_date + timedelta(days=-1)
    vol_sum_list = []
    close_price_list = []
    increase_rate_list = []
    rank_stock_list = pd.DataFrame(stock_list_ld)
    rank_stock_list.rename(columns={0: 'tscode'}, inplace=True)  # 重命名列名
    circulating_market_cap_list = []
    market_cap_list = []
    new_rank_stock_list = []
    for stock in rank_stock_list['tscode']:
        succ, vol_sum, close_price, increase_rate, cir_market_cap, market_cap = get_vol_close_increase(stock, trade_date_pre1d)
        if not succ:
            continue
        new_rank_stock_list.append(stock)
        circulating_market_cap_list.append(cir_market_cap)
        market_cap_list.append(market_cap)
        vol_sum_list.append(vol_sum)
        close_price_list.append(close_price)
        increase_rate_list.append(increase_rate)
    rank_stock_list['tscode'] = new_rank_stock_list
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
    # 根据评分排序
    totalcount.sort(key=lambda x: x[1])
    # 选取排名靠前的股票
    # 保留最多g.sellrank设置的个数股票代码返回
    final_list = [rank_stock_list['tscode'][totalcount[-1 - i][0]] for i in range(min(gv.sellrank, len(rank_stock_list)))]
    stock_list = final_list
    return stock_list

