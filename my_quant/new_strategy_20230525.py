import tushare as ts
import pandas as pd
from datetime import datetime
import math
import json
import tqdm
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import smtplib
import easyquotation
from email.mime.text import MIMEText
import matplotlib.dates as mdates
import copy

from functions.auto_trader import *
from functions.basic_functions import *
import functions.global_variables as gv


def send_email(content):
    code = 'MQCCPVCLWSLXAVRF'
    # 设置服务器所需信息
    # 163邮箱服务器地址
    mail_host = 'smtp.163.com'
    # 163用户名
    mail_user = 'h18675544580'
    # 邮件发送方邮箱地址
    sender = 'h18675544580@163.com'
    # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = ['6582496@qq.com']
    # 设置email信息
    # 邮件内容设置
    message = MIMEText(content, 'plain', 'utf-8')
    # 邮件主题
    message['Subject'] = time.asctime(time.localtime(time.time())) + '交易信息'
    # 发送方信息
    message['From'] = 'trade information'
    # 接受方信息
    message['To'] = receivers[0]

    # 登录并发送邮件
    try:
        smtpObj = smtplib.SMTP()
        # 连接到服务器
        smtpObj.connect(mail_host, 25)
        # 登录到服务器
        smtpObj.login(mail_user, code)
        # 发送
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        # 退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误

def get_real_price(stock):
    quotation = easyquotation.use('sina')
    price = quotation.real(stock[:6])[stock[:6]]['now']
    return price


def get_current_price(stock, is_back_testing):
    if is_back_testing:
        price = list(ts.pro_bar(ts_code=stock, adj=None, start_date=gv.trade_date, end_date=gv.today)['close'])[-1]
        factor_list = list(pro.adj_factor(ts_code=stock, start_date=gv.trade_date, end_date=gv.today)['adj_factor'])
        price = price * factor_list[-1] / factor_list[0]
    else:
        price = 10
    return price


def update_portfoli():
    positions = gv.portfolio['positions']
    stock_value = 0
    for stock in positions.keys():
        price = get_current_price(stock, True)
        positions[stock]['value_per'] = price
        positions[stock]['value'] = positions[stock]['value_per'] * positions[stock]['stock_number']
        stock_value = stock_value + positions[stock]['value']
    gv.portfolio['stock_value'] = stock_value
    gv.portfolio['total_value'] = stock_value + gv.portfolio['free_money']
    return


def sell_stock(stock):
    price = get_current_price(stock, True)
    stock_info = gv.portfolio['positions'][stock]
    gv.portfolio['free_money'] = price * stock_info['stock_number'] + gv.portfolio['free_money']
    del gv.portfolio['positions'][stock]
    return



def sell_stock_real(stock, hold_stock_list):
    price = get_real_price(stock)
    print(stock + ' price is ' + str(price))
    fix_result_order_id = gv.xt_trader.order_stock(gv.acc, stock, xtconstant.STOCK_SELL, hold_stock_list[stock], xtconstant.FIX_PRICE, price - 0.01)
    return fix_result_order_id


def buy_stock(stock, buy_num):
    price = get_current_price(stock, True)
    free_money = gv.portfolio['free_money'] - price * buy_num
    succ = False
    if free_money > 0:
        succ = True
    else:
        return succ
    gv.portfolio['free_money'] = gv.portfolio['free_money'] - price * buy_num
    gv.portfolio['positions'][stock] = {'value': buy_num * price, 'stock_number': buy_num, 'value_per': price}
    return succ

def buy_stock_real(stock, buy_num):
    price = get_real_price(stock)
    fix_result_order_id = gv.xt_trader.order_stock(gv.acc, stock, xtconstant.STOCK_BUY, buy_num, xtconstant.FIX_PRICE, price + 0.01)
    return fix_result_order_id





def my_adjust_position():
    # My selling method
    hold_stock = copy.deepcopy(list(gv.portfolio['positions'].keys()))
    for stock in hold_stock:
        if stock not in gv.g_chosen_stock_list:
            sell_stock(stock)
    update_portfoli()

    # My buying method
    free_money = gv.portfolio['free_money']
    hold_stock_num = len(gv.portfolio['positions'])
    need_buy_num = gv.buy_stock_count - hold_stock_num
    if need_buy_num == 0:
        return
    need_buy_money_each_stock = free_money * 0.99 / need_buy_num
    for stock in gv.g_chosen_stock_list:
        if stock in gv.portfolio['positions'].keys():
            continue
        if hold_stock_num >= gv.buy_stock_count:
            break
        price = get_current_price(stock, True)
        need_buy_num_each_stock = int(0.01 * need_buy_money_each_stock / price) * 100
        succ = buy_stock(stock, need_buy_num_each_stock)
        hold_stock_num = len(gv.portfolio['positions'])
    update_portfoli()
    return



def start_miniQMT():
    # session_id为会话编号，策略使用方对于不同的Python策略需要使用不同的会话编号
    session_id = 123456
    xt_trader = XtQuantTrader(gv.path, session_id)
    # StockAccount可以用第二个参数指定账号类型，如沪港通传'HUGANGTONG'，深港通传'SHENGANGTONG'
    acc = StockAccount(gv.account_num, 'STOCK')
    # 创建交易回调类对象，并声明接收回调
    callback = MyXtQuantTraderCallback()
    xt_trader.register_callback(callback)
    # 启动交易线程
    xt_trader.start()
    # 建立交易连接，返回0表示连接成功
    connect_result = xt_trader.connect()
    if connect_result != 0:
        import sys
        sys.exit('链接失败，程序即将退出 %d' % connect_result)
    # 对交易回调进行订阅，订阅后可以收到交易主推，返回0表示订阅成功
    subscribe_result = xt_trader.subscribe(acc)
    if subscribe_result != 0:
        print('账号订阅失败 %d' % subscribe_result)
    gv.xt_trader = xt_trader
    gv.acc = acc
    return True

def my_adjust_position_real():
    succ = start_miniQMT()
    if not succ:
        return False
    # Update inforamtion
    positions = gv.xt_trader.query_stock_positions(gv.acc)
    hold_stock_list = {}
    for posit in positions:
        if posit.volume > 0:
            hold_stock_list[posit.stock_code] = posit.volume
    # My selling method
    hold_stock = copy.deepcopy(hold_stock_list)
    print(hold_stock_list)
    for stock in hold_stock:
        if stock not in gv.g_chosen_stock_list:
            sell_stock_real(stock, hold_stock_list)

    # Update inforamtion
    positions = gv.xt_trader.query_stock_positions(gv.acc)
    asset = gv.xt_trader.query_stock_asset(gv.acc)
    free_money = asset.cash
    print('free money is')
    print(free_money)
    hold_stock_list = {}
    for posit in positions:
        if posit.volume > 0:
            hold_stock_list[posit.stock_code] = posit.volume
    gv.total_value = asset.total_asset
    hold_stock_num = len(hold_stock_list)
    need_buy_num = gv.buy_stock_count - hold_stock_num
    print(need_buy_num)
    if need_buy_num == 0:
        return
    need_buy_money_each_stock = free_money * 0.99 / need_buy_num
    for stock in gv.g_chosen_stock_list:
        if stock in hold_stock_list:
            continue
        if hold_stock_num >= gv.buy_stock_count:
            break
        price = get_real_price(stock)
        need_buy_num_each_stock = int(0.01 * need_buy_money_each_stock / price) * 100
        # print(price, need_buy_num_each_stock)
        succ = buy_stock_real(stock, need_buy_num_each_stock)
        if succ:
            hold_stock_list[stock] = need_buy_num_each_stock
        hold_stock_num = len(hold_stock_list)
        print(hold_stock_num)
    return True



def run_monthly():
    print('begin to run monthly method')
    gv.g_month_chosen_stock_list = get_stock_list(gv.trade_date_time)
    print('After pe pb filter, the length of stock list is:')
    df = pd.DataFrame()
    for stock in gv.g_month_chosen_stock_list:
        succ, cur_df = get_finance_data(stock, gv.trade_date_time)
        if not succ:
            continue
        df = pd.concat([df, cur_df])
    ffscore_filted_stock = ffscore_stock(df, gv.score, gv.g_month_chosen_stock_list)
    gv.g_month_chosen_stock_list = ffscore_filted_stock
    print('After ffscore filter, the length of stock list is:')
    print(len(gv.g_month_chosen_stock_list))
    new_stock_list = []
    for stock in gv.g_month_chosen_stock_list:
        print(stock)
        if not (stock[0] == '4' or stock[0] == '8' or stock[:2] == '68' or stock[:2] == '30'):
            new_stock_list.append(stock)
    gv.g_month_chosen_stock_list = new_stock_list
    with open('D:/pythonProject/Quant/my_quant/' + str(gv.trade_date) + 'month_notkcbjcy.json', 'w') as f:
        json.dump(gv.g_month_chosen_stock_list, f)
    with open('D:/pythonProject/Quant/my_quant/' + str(gv.trade_date) + 'month_notkcbjcy.json', 'r') as f:
        gv.g_month_chosen_stock_list = json.load(f)


def run_daily():
    print('begin to run daily method')
    rank_m_m_filted_stock = get_stock_rank_m_m(gv.g_chosen_stock_list, gv.trade_date_time)
    gv.g_chosen_stock_list = rank_m_m_filted_stock
    print('After rank_m_m filter, the length of stock list is:')
    print(len(gv.g_chosen_stock_list))
    print(gv.g_chosen_stock_list)


def main():
    ts.set_token('c7469f373bc382729fcd19f4b014a58b5679bb0578c8ee9841aea01c')
    pro = ts.pro_api()
    # today = datetime.now().strftime('%Y%m%d')
    # gv.today = today
    # with open('D:/pythonProject/Quant/my_quant/stock_list.json', 'r') as f:
    #     gv.g_chosen_stock_list = json.load(f)
    # run_daily()
    # gv.trade_date = datetime.now().strftime('%Y%m%d')
    # gv.trade_date_time = datetime.strptime(gv.trade_date, '%Y%m%d')
    # gv.daily_df = pro.daily(trade_date=gv.trade_date_time.strftime('%Y%m%d'))
    # update_portfoli()
    # print(gv.portfolio)

    # back testing
    is_back_testing = True
    begin_date = '20220301'
    end_date = '20230601'
    df = pro.trade_cal(exchange='', start_date=begin_date, end_date=end_date)
    gv.cal_date = pro.trade_cal(exchange='', start_date=(datetime.strptime(begin_date, '%Y%m%d') + timedelta(days=-10)).strftime('%Y%m%d'),
                                end_date=end_date)
    df = df[df['is_open'] == 1]
    trade_date_list = list(df['cal_date'])
    trade_date_list.reverse()
    increase_rate_list = []
    date_list = []
    begin_value = gv.portfolio['total_value']
    for i, one_date in enumerate(trade_date_list):
        print('today is ' + one_date)
        gv.trade_date = one_date
        gv.trade_date_time = datetime.strptime(gv.trade_date, '%Y%m%d')
        gv.daily_df = pro.daily(trade_date=gv.trade_date_time.strftime('%Y%m%d'))
        is_first_trade_date = False
        if gv.trade_date[4:6] != trade_date_list[i - 1][4:6] or i == 0:
            is_first_trade_date = True
        if is_first_trade_date:
            run_monthly()
        gv.g_chosen_stock_list = gv.g_month_chosen_stock_list
        if is_first_trade_date:
            run_daily()
        send_email(str(gv.g_chosen_stock_list))
        my_adjust_position()
        print('today is ' + one_date)
        print('Total value is:')
        print(gv.portfolio['total_value'])
        print(gv.portfolio)
        print('increase rate is:')
        increase_rate = 100 * (gv.portfolio['total_value'] / begin_value - 1)
        increase_rate_list.append(increase_rate)
        date_list.append(one_date)
        print(increase_rate_list)

    print(increase_rate_list)
    my_x_ticks = np.arange(0, len(increase_rate_list), len(increase_rate_list) // 4)
    plt.xticks(my_x_ticks)
    plt.plot(date_list, increase_rate_list)
    plt.show()
    plt.savefig('D:/pythonProject/Quant/my_quant/' + begin_date + '_' + end_date + '.png')

    # begin_date = '20230601'
    # end_date = '20230601'
    # df = pro.trade_cal(exchange='', start_date=begin_date, end_date=end_date)
    # gv.cal_date = pro.trade_cal(exchange='', start_date=(datetime.strptime(begin_date, '%Y%m%d') + timedelta(days=-10)).strftime('%Y%m%d'),
    #                             end_date=end_date)
    # df = df[df['is_open'] == 1]
    # trade_date_list = list(df['cal_date'])
    # trade_date_list.reverse()
    # now_day_time = datetime.now()
    # gv.trade_date_time = now_day_time
    # gv.trade_date = now_day_time.strftime('%Y%m%d')
    # # run_monthly()
    # # with open('D:/pythonProject/Quant/my_quant/' + str(gv.trade_date[:-2]) + 'month.json', 'r') as f:
    # #     gv.g_month_chosen_stock_list = json.load(f)
    # # gv.g_chosen_stock_list = copy.deepcopy(gv.g_month_chosen_stock_list)
    # # run_daily()
    # # with open('D:/pythonProject/Quant/my_quant/' + str(gv.trade_date) + '.json', 'w') as f:
    # #     json.dump(gv.g_chosen_stock_list, f)
    #
    # with open('D:/pythonProject/Quant/my_quant/' + str(gv.trade_date) + '.json', 'r') as f:
    #     gv.g_chosen_stock_list = json.load(f)
    # # send_email(str(gv.g_chosen_stock_list))
    # my_adjust_position_real()





def test_func():
    gv.trade_date_time = datetime.strptime('20230412', '%Y%m%d')
    gv.daily_df = pro.daily(trade_date=gv.trade_date_time.strftime('%Y%m%d'))
    gv.portfolio = {'positions': {'688659.SH': {'value': 41648.0, 'stock_number': 3800, 'value_per': 10.96},
                                  '688013.SH': {'value': 47943.0, 'stock_number': 2100, 'value_per': 22.83},
                                  '605003.SH': {'value': 42560.0, 'stock_number': 1900, 'value_per': 22.4},
                                  '605088.SH': {'value': 45084.0, 'stock_number': 3400, 'value_per': 13.26}},
                    'total_value': 184659.0, 'free_money': 7424.0, 'stock_value': 177235.0}
    print(gv.portfolio)
    gv.g_chosen_stock_list = ['688658.SH', '688012.SH', '605001.SH', '603967.SH', '300563.SZ', '605098.SH', '603758.SH',
                              '300997.SZ']
    my_adjust_position()
    print(gv.portfolio)


if __name__ == '__main__':
    main()


