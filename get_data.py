import json
import time
import os
import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import tqdm
from alpha101.feature_generate import *

#设置token
ts.set_token('1683668800a1289c82d373871e972a4a18fc5913247bf5c0819272d1')
#初始pro对象
pro = ts.pro_api()

global_dic = dict()

def vwap(df):
    """
    volume-weighted average price
    """
    return (df.volume * df.close) / df.volume

def get_stock_list():
    stock_df = pro.stock_basic(exchange='', list_status='L')
    stock_list_name = []
    stock_list = []
    for index in stock_df.index:
        if not ('ST' in stock_df['name'].get(index)
                or '*' in stock_df['name'].get(index) or 'BJ' in stock_df['ts_code'].get(index)):
            stock_list_name.append(stock_df['name'].get(index))
            stock_list.append(stock_df['ts_code'].get(index))
    return stock_list

def get_trade_date(start_date, end_date):
    trade_df = pro.query('trade_cal', start_date=start_date, end_date=end_date)
    trade_date = []
    for index in trade_df.index:
        if trade_df['is_open'].get(index) == 1:
            trade_date.append(trade_df['cal_date'].get(index))
    return trade_date



def get_global_dic(global_dic, stock_list, trade_list):
    for trade_ in trade_list:
        for stock in stock_list:
            if trade_ not in global_dic:
                global_dic[trade_] = dict()
            if stock not in global_dic[trade_]:
                global_dic[trade_][stock] = dict()
    return global_dic

def get_daily_factor(ts_code, start_date, end_date, global_dic):
    factors = ['turnover_rate', 'turnover_rate_f', 'volume_ratio', 'pe', 'pe_ttm', 'pb',
               'ps', 'ps_ttm', 'dv_ratio', 'dv_ttm']
    daily_df = pro.daily_basic(ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        fields='ts_code,trade_date,' + ','.join(factors))
    keys = list(daily_df.keys())
    for index in daily_df.index:
        for key in keys:
            if key == 'ts_code' or key == 'trade_date':
                continue
            if not daily_df[key].get(index) or daily_df[key].get(index) == float('nan'):
                global_dic[daily_df['trade_date'].get(index)][ts_code][key] = 0
            else:
                global_dic[daily_df['trade_date'].get(index)][ts_code][key] \
                    = daily_df[key].get(index)
    return global_dic

def get_stk_factor(ts_code, start_date, end_date, global_dic):
    factors = ['pct_change', 'macd_dif', 'macd_dea', 'macd', 'kdj_k', 'kdj_d',
               'kdj_j', 'rsi_6', 'rsi_12', 'rsi_24', 'boll_upper', 'boll_mid', 'boll_lower', 'cci']
    stk_df = pro.stk_factor(ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        fields='ts_code,trade_date,' + ','.join(factors))
    keys = list(stk_df.keys())
    for index in stk_df.index:
        for key in keys:
            if key == 'ts_code' or key == 'trade_date':
                continue
            if not stk_df[key].get(index) or stk_df[key].get(index) == float('nan'):
                global_dic[stk_df['trade_date'].get(index)][ts_code][key] = 0
            else:
                global_dic[stk_df['trade_date'].get(index)][ts_code][key] \
                    = stk_df[key].get(index)
    return global_dic


def get_income_data(ts_code, start_date, end_date, global_dic):
    factors = ['comp_type', 'end_type', 'basic_eps', 'diluted_eps', 'total_revenue'
               , 'revenue', 'int_income', 'prem_earned', 'comm_income', 'n_commis_income'
               , 'n_oth_income', 'n_oth_b_income', 'prem_income', 'out_prem', 'une_prem_reser'
               , 'reins_income', 'n_sec_tb_income', 'n_sec_uw_income', 'n_asset_mg_income'
               , 'oth_b_income', 'fv_value_chg_gain', 'invest_income', 'ass_invest_income'
               , 'forex_gain', 'total_cogs', 'oper_cost', 'int_exp', 'comm_exp', 'biz_tax_surchg'
               , 'sell_exp', 'admin_exp', 'fin_exp', 'assets_impair_loss', 'prem_refund'
               , 'compens_payout', 'reser_insur_liab', 'div_payt', 'reins_exp', 'oper_exp'
               , 'compens_payout_refu', 'insur_reser_refu', 'reins_cost_refund', 'other_bus_cost'
               , 'operate_profit', 'non_oper_income', 'non_oper_exp', 'nca_disploss', 'total_profit'
               , 'income_tax', 'n_income', 'n_income_attr_p', 'minority_gain', 'oth_compr_income'
               , 't_compr_income', 'compr_inc_attr_p', 'compr_inc_attr_m_s', 'ebit', 'ebitda'
               , 'insurance_exp', 'undist_profit', 'distable_profit', 'rd_exp']
    stk_df = pro.income(ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        fields='ts_code,f_ann_date,' + ','.join(factors))
    print(stk_df)
    keys = list(stk_df.keys())
    for index in stk_df.index:
        for key in keys:
            if key == 'ts_code' or key == 'trade_date':
                continue
            if not stk_df[key].get(index) or stk_df[key].get(index) == float('nan'):
                global_dic[stk_df['trade_date'].get(index)][ts_code][key] = 0
            else:
                global_dic[stk_df['trade_date'].get(index)][ts_code][key] \
                    = stk_df[key].get(index)
    return global_dic

def get_alpha(ts_code, start_date, end_date, global_dic):

    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    new_df = pd.DataFrame()
    new_df['open'] = df['open']
    new_df['high'] = df['high']
    new_df['low'] = df['low']
    new_df['close'] = df['close']
    new_df['volume'] = df['vol']
    new_df['returns'] = df['pct_chg']
    new_df['vwap'] = vwap(new_df)
    data_df =get_all_factors(new_df)
    data_df['trade_date'] = df.trade_date
    data_df['ts_code'] = df.ts_code
    keys = list(data_df.keys())
    for index in data_df.index:
        for key in keys:
            if key == 'ts_code' or key == 'trade_date':
                continue
            if not data_df[key].get(index) or data_df[key].get(index) == float('nan'):
                global_dic[data_df['trade_date'].get(index)][ts_code][key] = 0.
            else:
                global_dic[data_df['trade_date'].get(index)][ts_code][key] \
                    = float(data_df[key].get(index))
    return global_dic

def get_data_by_date_stock(trade_list, stock_list, global_dic):
    start_time = None
    for num, stock in enumerate(tqdm.tqdm(stock_list)):
        get_stk_factor(stock, trade_list[-1], trade_list[0], global_dic)
        get_daily_factor(stock, trade_list[-1], trade_list[0], global_dic)
        get_alpha(stock, trade_list[-1], trade_list[0], global_dic)
        if num % 100 == 0:
            start_time = time.time()
        if num % 100 == 99:
            if time.time() - start_time < 60:
                time.sleep(10)
    return global_dic

def get_data_by_date_stock_income(trade_list, stock_list, global_dic):
    start_time = None
    for num, stock in enumerate(stock_list):
        get_income_data(stock, trade_list[-1], trade_list[0], global_dic)
        if num % 100 == 0:
            start_time = time.time()
        if num % 100 == 99:
            if time.time() - start_time < 60:
                time.sleep(10)
        print(stock)
    return global_dic

def get_pct_chg_label(trade_list, stock_list, global_dic):
    for stock in tqdm.tqdm(stock_list):
        df_pct_chg = ts.pro_bar(ts_code=stock, adj='qfq',
                        start_date=trade_list[-1], end_date=trade_list[0])
        if df_pct_chg is None:
            continue
        for index in df_pct_chg.index:
            if index > len(trade_list) - 21:
                continue
            trade_date = df_pct_chg['trade_date'].get(index + 20)
            if trade_date is None:
                continue
            close_goal = df_pct_chg['close'].get(index)
            close_ = df_pct_chg['close'].get(index + 20)
            if close_goal and close_:
                global_dic[trade_date][stock]['label'] = 100 * (close_goal / close_ - 1.0)


def save_data(data_path, global_dic):
    new_dic = dict()
    for key in global_dic.keys():
        new_stock_dic = dict()
        for stock_key in global_dic[key].keys():
            if 'label' in global_dic[key][stock_key]:
                new_stock_dic[stock_key] = global_dic[key][stock_key]
        new_dic[key] = new_stock_dic
        with open(os.path.join(data_path, key + '.json'), 'w') as f:
            json.dump(new_dic[key], f)







def lr_train(X,Y):
    from sklearn.linear_model import LinearRegression
    lr = LinearRegression()
    lr.fit(X, Y)
    return lr

def xgboost_train(X, Y):
    import xgboost as xgb
    model = xgb.XGBClassifier(max_depth=5, n_estimators=500, min_child_weight=1, subsample=0.8,
                             colsample_bytree=0.8, gamma=0, reg_alpha=0, reg_lambda=1, learning_rate=0.1)
    model.fit(X, Y)
    return model

stock_list = get_stock_list()
trade_list = get_trade_date('20220101', '20221231')
#
# file_path = 'D:/ts_data'
file_path = 'D:/ts_data_alpha'
stock_list = stock_list
# # #
global_dic = get_global_dic(global_dic, stock_list, trade_list)
global_dic = get_data_by_date_stock(trade_list[20:], stock_list, global_dic)
get_pct_chg_label(trade_list, stock_list, global_dic)
save_data(file_path, global_dic)


