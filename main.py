import easytrader
import easyquotation
import tushare as ts
import akshare as ak
import time
import schedule
import os
import win32api
import win32con
import smtplib
from email.mime.text import MIMEText
from matplotlib import pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import optuna



class Account:
    def __init__(self,totalmoney,strategy_name):
        self.balance = {'可用金额': totalmoney, '总资产': totalmoney}
        self.position = dict()
        self.values = [0]
        self.strategy_name = strategy_name
        self.values_his = [totalmoney]

class Autotrader:
    def __init__(self):
        self.user = easytrader.use('universal_client')
        self.g = dict()
        self.pro = ts.pro_api()
        self.unit = 3600 * 24
        self.before_market_time = 9
        self.market_time = 10
        ts.set_token('1683668800a1289c82d373871e972a4a18fc5913247bf5c0819272d1')
        self.g['etf'] = []
        self.g['etfinit'] = ['512010.SH', '161903.SZ', '161005.SZ',
                             '162605.SZ', '169104.SZ', '162006.SZ', '161810.SZ', '163417.SZ']
        self.g['days'] = 20
        self.g['days_filter'] = 500
        self.g['Nasdaq'] = '513100.SH'
        self.g['CYB'] = '159915.SZ'
        self.g['length_candidate'] = 5
        self.g['balance'] = {'可用金额': 0, '总资产': 0}
        self.g['position'] = []
        self.g['is_open'] = 0
        self.trade_information = ''

    def get_rate(self,fund,days):
        if fund==None:
            return -1
        # df = self.pro.fund_daily(ts_code=fund)
        df = ak.fund_etf_hist_em(symbol="513100")
        close_data = list(df['close'])
        if len(close_data)<days:
            return -1
        close_data = close_data[:days]

        factors = list(self.pro.fund_adj(ts_code=fund)['adj_factor'])[:days]
        quotation = easyquotation.use('sina')
        price = quotation.real(fund[:6])[fund[:6]]['now']
        rate = (factors[0]*price-factors[-1]*close_data[-1])/(factors[-1]*close_data[-1])
        # print(close_data[0])
        return rate

    def get_rate_close_only(self, fund,days):
        if fund==None:
            return -1
        df = self.pro.fund_daily(ts_code=fund)
        close_data = list(df['close'])
        if len(close_data)<days:
            return -1
        close_data = close_data[:days]
        print(close_data)
        return -1

    def insert(self,stack,rate):
        pre = 0
        last = len(stack)-1
        while pre<=last:
            mid = (pre+last)//2
            if stack[mid]==rate:
                return mid
            elif stack[mid]>rate:
                pre = mid +1
            else:
                last = mid - 1
        return pre

    def get_fund(self):
        df_code_list = self.g['etfinit']
        stack = [-1 for i in range(self.g['length_candidate'])]
        re_lofs = [None for i in range(self.g['length_candidate'])]
        for lof in df_code_list:
            # self.trade_information = self.trade_information + '\n  ' + str(lof) + ' ' + str(self.g['days_filter']) + '天涨幅为' + str(
            #     self.get_rate(lof, self.g['days_filter']))
            if self.get_rate(lof,self.g['days_filter'])>0.3:
                rate = self.get_rate(lof,self.g['days'])
                if rate > stack[-1]:
                    index = self.insert(stack,rate)
                    stack = stack[:index] + [rate]+stack[index:-1]
                    re_lofs = re_lofs[:index] + [lof] + re_lofs[index:-1]
        return re_lofs


    def convert_position(self,position_ori):
        position = dict()
        for po in position_ori:
            position[po['证券代码']] = po['可用余额']
        return position

    def sell_all(self,price,stock_num,balance,position):
        if stock_num[:6] not in position:
            print('下单失败，'+stock_num+"不在持仓中")
            return False
        else:
            amount = position[stock_num[:6]]
            self.user.sell(stock_num[:6],None,amount)
            balance['可用金额'] = balance['可用金额'] + price*amount
            del position[stock_num[:6]]
            print('以'+str(price)+'卖出'+str(amount)+'份'+str(stock_num)+'增加'+str(amount*price)+'元')
            print('新账户信息为：')
            print(balance, position)
            self.trade_information = self.trade_information + '\n, ' +time.asctime(time.localtime(time.time())) + '\n以'+str(price)+\
                                     '卖出'+str(amount)+'份'+str(stock_num)+'增加'+str(amount*price)+'元, 剩余账户信息为： '+str(balance)+'持仓: '+str(position)
            return True
    def buy_all(self,price,stock_num,balance,position,total_money):
        print(price, total_money)
        amount = 100 * (int((total_money - 1000) / (price * 100)))
        if amount<100:
            print("资金不足购买100股票，购买失败")
            return False
        if price*amount>balance['可用金额']:
            print('下单失败，可用金额小于下单金额，检查是否有订单堆积')
            return False
        while amount > 900000:
            self.user.buy(stock_num[:6], None, 900000)
            amount = amount - 900000
        self.user.buy(stock_num[:6],None,amount)
        position[stock_num[:6]] = amount
        balance['可用金额'] = balance['可用金额'] - price*amount
        print('以' + str(price) + '买入' + str(amount) + '份' + str(stock_num) + '花费' + str(amount * price) + '元')
        print('新账户信息为：')
        print(balance,position)
        self.trade_information = self.trade_information + '\n, ' + time.asctime( time.localtime(time.time()) )+'\n以' + str(price) + '买入' + str(amount) \
                                 + '份' + str(stock_num) + '花费' + str(amount * price) + '元, 剩余账户信息为： '+str(balance)+'持仓: '+str(position)
        return True

    def open_tonghuashun_exe(self):
        self.killexe()
        path = "D:/tonghuashun/hexin.exe"
        win32api.ShellExecute(0, 'open', path, '', '', 1)
        print('打开同花顺软件')
        time.sleep(5)
        win32api.SetCursorPos([1400,500])
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(5)
        win32api.keybd_event(123, 0, 0, 0)
        win32api.keybd_event(123, 0, win32con.KEYEVENTF_KEYUP, 0)
        print('打开交易软件')
        time.sleep(5)
        return


    def check_open(self):
        localtime = time.localtime(time.time())
        year = localtime.tm_year
        month = localtime.tm_mon
        day = localtime.tm_mday
        if month < 10:
            month_s = '0' + str(month)
        else:
            month_s = str(month)
        if day < 10:
            day_s = '0' + str(day)
        else:
            day_s = str(day)
        today = str(year) + month_s + day_s
        print(today)
        self.g['is_open'] = list(self.pro.query('trade_cal', start_date=today, end_date=today)['is_open'])[0]
        # self.g['is_open'] = 1
        print(self.g['is_open'])
        self.trade_information = ''
        return

    def before_market(self):
        self.user.connect(r'D:\tonghuashun\xiadan.exe')
        self.user.enable_type_keys_for_editor()
        if self.g['is_open']==0:
            print('不开盘')
            return
        #获取候选ETF列表
        self.g['etf'] = self.get_fund()
        print('ETF候选集为:' + str(self.g['etf']))
        #获取当前账户信息
        self.g['balance'] = self.user.balance
        self.g['position'] = self.user.position
        print('初始账户信息为：')
        print(self.g['balance'], self.g['position'])
        return

    def market(self, params):
        buy_th = params['buy_th']
        sell_th = params['sell_th']
        days = params['days']
        if self.g['is_open']==0:
            print('不开盘')
            return
        balance = self.g['balance']
        position = self.convert_position(self.g['position'])
        half_value = balance['总资产']
        # sub_value = half_value / len(self.g['etf'])
        print('Total value is: ' + str(half_value * 2))
        quotation = easyquotation.use('sina')
        current_rate = self.get_rate(self.g['CYB'], days)
        if current_rate > buy_th:
            information = str(days) + '创业板涨幅'+str(current_rate)+',超过' + str(buy_th * 100) + '%，以进攻策略持有创业板，空仓纳斯达克'
            print(information)
            self.trade_information = self.trade_information + '\n  ' + information
            self.trade_information = self.trade_information + '\n  ' + str(self.g['CYB']) + ' ' + str(days) + '天涨幅为' + str(
                self.get_rate(self.g['CYB'], days))
            if self.g['Nasdaq'][:6] in position:
                price = quotation.real(self.g['Nasdaq'][:6])[self.g['Nasdaq'][:6]]['now']
                # if self.sell_all(price, self.g['Nasdaq'], balance, position):
                #     self.trade_information = self.trade_information + '\n  成功卖出纳斯达克'
                #     print('成功卖出纳斯达克')
                #     self.before_market()
            # time.sleep(60)
            balance = self.g['balance']
            half_value = balance['可用金额']
            if self.g['CYB'][:6] not in position:
                price = quotation.real(self.g['CYB'][:6])[self.g['CYB'][:6]]['now']
                # if self.buy_all(price, self.g['CYB'], balance, position, half_value):
                #     self.trade_information = self.trade_information + '\n  成功买入创业板'
                #     print('成功买入创业板')
                #     self.before_market()
        elif current_rate < sell_th:
            information = str(days) + '创业板涨幅'+str(current_rate)+',低于' + str(sell_th * 100) + '%,以防守策略半仓纳斯达克，空仓创业板'
            print(information)
            self.trade_information = self.trade_information + '\n  ' + information
            if self.g['CYB'][:6] in position:
                price = quotation.real(self.g['CYB'][:6])[self.g['CYB'][:6]]['now']
                # if self.sell_all(price, self.g['CYB'], balance, position):
                #     self.trade_information = self.trade_information + '\n  成功卖出创业板'
                #     print('成功卖出创业板')
                #     self.before_market()
        else:
            information = '\n' + str(days) + '天创业板涨幅'+str(current_rate) + '高于' + str(sell_th) + ', 低于' + str(buy_th) + ', 持仓不动。'
            self.trade_information = self.trade_information + information
            print(information)

        if self.g['Nasdaq'][:6] not in position and self.g['CYB'][:6] not in position:
            self.trade_information = self.trade_information + '\n  ' + str(self.g['Nasdaq']) + ' ' + str(
                self.g['days']) + '天涨幅为' + str(
                self.get_rate(self.g['Nasdaq'], self.g['days']))
            self.trade_information = self.trade_information + '\n  成功买入纳斯达克'
            price = quotation.real(self.g['Nasdaq'][:6])[self.g['Nasdaq'][:6]]['now']
            # if self.buy_all(price, self.g['Nasdaq'], balance, position, half_value):
            #     self.trade_information = self.trade_information + '\n  成功买入纳斯达克'
            #     print('成功买入纳斯达克')
            #     self.before_market()

        # #EFT集合，使用一半资金
        # for lof in self.g['etfinit']:
        #     if self.get_rate(lof, self.g['days']) < -0.05 and lof[:6] in position:
        #         print(lof + '跌幅高于5%，卖出')
        #         price = quotation.real(lof[:6])[lof[:6]]['now']
        #         if self.sell_all(price, lof, balance, position):
        #             print('成功卖出'+str(lof))
        # if balance['可用金额'] > 0:
        #     for lof in self.g['etf']:
        #         if lof==None:
        #             continue
        #         self.trade_information = self.trade_information + '\n  ' + str(lof)+' ' +str(self.g['days']) + '天涨幅为' +str(self.get_rate(lof, self.g['days']))
        #         if self.get_rate(lof, self.g['days']) > 0.05 and lof[:6] not in position:
        #             print(lof + '涨幅高于5%，买入')
        #             self.trade_information = self.trade_information + '\n  '+str(lof)+'涨幅高于5%'
        #             price = quotation.real(lof[:6])[lof[:6]]['now']
        #             if self.buy_all(price, lof, balance, position, sub_value):
        #                 print('成功买入'+str(lof))
        # print('剩余现金：' + str(balance['可用金额']))
        print('最终账户信息为：')
        print(balance,position)
        self.send_email(time.asctime( time.localtime(time.time()) )+self.trade_information+
                        '\n最终账户信息为：'+str(balance)+'\n 持仓: '+str(position))
        return

    def killexe(self):
        os.system('taskkill /IM hexin.exe /F')
        os.system('taskkill /IM xiadan.exe /F')
    def send_email(self,content):
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
        message['Subject'] = time.asctime( time.localtime(time.time()) )+'交易信息'
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

    def get_bar(self,fund, start_date, end_date):
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        final_close_data = []
        final_factors = []
        trade_dates_price = []
        trade_dates_factors = []
        if start_year == end_year:
            df = self.pro.fund_daily(ts_code=fund, start_date=start_date, end_date=end_date)
            close_data = list(df['close'])
            factors = list(self.pro.fund_adj(ts_code=fund, start_date=start_date, end_date=end_date)['adj_factor'])
            trade_dates_price = list(self.pro.fund_daily(ts_code=fund, start_date=start_date, end_date=end_date)[
                                         'trade_date']) + trade_dates_price
            trade_dates_factors = list(self.pro.fund_adj(ts_code=fund, start_date=start_date, end_date=end_date)[
                                           'trade_date']) + trade_dates_factors
            final_close_data = close_data + final_close_data
            final_factors = factors + final_factors
        else:
            year_ = start_year
            while year_ <= end_year:
                if year_ == start_year:
                    s_date = str(year_) + start_date[4:]
                    e_date = str(year_) + '1231'
                elif year_ == end_year:
                    s_date = str(year_) + '0101'
                    e_date = str(year_) + end_date[4:]
                else:
                    s_date = str(year_) + '0101'
                    e_date = str(year_) + '1231'
                close_data = list(self.pro.fund_daily(ts_code=fund, start_date=s_date, end_date=e_date)['close'])
                trade_dates_price = list(
                    self.pro.fund_daily(ts_code=fund, start_date=s_date, end_date=e_date)['trade_date']) + trade_dates_price
                trade_dates_factors = list(
                    self.pro.fund_adj(ts_code=fund, start_date=s_date, end_date=e_date)['trade_date']) + trade_dates_factors
                final_close_data = close_data + final_close_data
                year_ = year_ + 1
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
        dates_vec = list(self.pro.query('trade_cal', start_date=start_date, end_date=end_date)['cal_date'])
        opens = list(self.pro.query('trade_cal', start_date=start_date, end_date=end_date)['is_open'])
        dates = dict()
        # print(factor_dic)
        for i in range(len(dates_vec)):
            dates[dates_vec[i]] = opens[i]
        pre_price = 0
        for date in dates:
            if dates[date] == 0:
                continue
            if date in price_dic and date in factor_dic:
                new_values[date] = price_dic[date] * factor_dic[date] / final_factors[-1]
                pre_price = new_values[date]
            else:
                new_values[date] = pre_price

        return new_values


    def back_testing(self,start,end,totalmoney,benchmark):
        date_start = '20110101'
        dates_vec = list(self.pro.query('trade_cal', start_date=date_start, end_date=end)['cal_date'])
        opens = list(self.pro.query('trade_cal', start_date=date_start, end_date=end)['is_open'])

        # print(factor_dic)
        account1 = Account(totalmoney,'CYB—NASDAQ-ETF')
        account2 = Account(totalmoney,'CYB—NASDAQ')
        prices =  dict()
        for fund in self.g['etfinit']:
            prices[fund[:6]] = self.get_bar(fund,date_start,end)
        prices[self.g['Nasdaq'][:6]] = self.get_bar(self.g['Nasdaq'], date_start, end)
        prices[self.g['CYB'][:6]] = self.get_bar(self.g['CYB'], date_start, end)
        # for key in prices:
        #     print(key)
        def get_rate_pri(fund,days,today,dates_open,prices):
            if fund == None:
                return -1
            index_today = dates_open.index(today)

            last_today = dates_open[index_today-days]
            # print(today,last_today)
            # print(prices[fund][today],prices[fund][last_today])
            if prices[fund][last_today]==0:
                return -1
            rate = (prices[fund][today] - prices[fund][last_today]) / prices[fund][last_today]
            return rate

        def sell(price, stock_num, balance, position):
            if stock_num[:6] not in position:
                print('下单失败，' + stock_num + "不在持仓中")
                return False
            else:
                amount = position[stock_num[:6]]
                balance['可用金额'] = balance['可用金额'] + price * amount
                del position[stock_num[:6]]
                print('以' + str(price) + '卖出' + str(amount) + '份' + str(stock_num) + '增加' + str(amount * price) + '元')
                print('新账户信息为：')
                print(balance, position)
                return True

        def buy(price,stock_num,balance,position,total_money):
            amount = 100 * (total_money // (price * 100))
            if amount < 100:
                print("资金不足购买100股票，购买失败")
                return False
            if price * amount > balance['可用金额']:
                print('下单失败，可用金额小于下单金额，检查是否有订单堆积')
                return False
            position[stock_num[:6]] = amount
            balance['可用金额'] = balance['可用金额'] - price * amount
            print('以' + str(price) + '买入' + str(amount) + '份' + str(stock_num) + '花费' + str(amount * price) + '元')
            print('新账户信息为：')
            print(balance, position)
            return True


        def renew(balance,position,today,prices):
            totoal_value = 0
            for key in position:
                totoal_value = totoal_value + prices[key][today]*position[key]
            totoal_value = totoal_value+balance['可用金额']
            balance['总资产'] = totoal_value
            return


        def do_market(balance,position,today,dates_open,prices):
            half_value = balance['总资产']/2
            sub_value = half_value / len(self.g['etf'])
            print('Total value is: ' + str(half_value * 2))
            increase_rate = get_rate_pri(self.g['CYB'][:6], self.g['days'],today,dates_open,prices)
            if increase_rate > 0.07:
                print('创业板涨幅为'+str(increase_rate)+',超过7%，以进攻策略持有创业板，空仓纳斯达克')
                if self.g['Nasdaq'][:6] in position:
                    price = prices[self.g['Nasdaq'][:6]][today]
                    if sell(price, self.g['Nasdaq'], balance, position):
                        print('成功卖出纳斯达克')

                if self.g['CYB'][:6] not in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if buy(price, self.g['CYB'], balance, position, half_value):
                        print('成功买入创业板')
            elif increase_rate < 0:
                print('创业板涨幅为'+str(increase_rate)+',低于0%,以防守策略半仓纳斯达克，空仓创业板')
                if self.g['CYB'][:6] in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if sell(price, self.g['CYB'], balance, position):
                        print('成功卖出创业板')
            else:
                print('创业板涨幅为'+str(increase_rate)+',高于0%，低于7%，持仓不动')
            if self.g['Nasdaq'][:6] not in position and self.g['CYB'][:6] not in position:
                price = prices[self.g['Nasdaq'][:6]][today]
                if buy(price, self.g['Nasdaq'], balance, position, half_value):
                    print('成功买入纳斯达克')

            # EFT集合，使用一半资金
            for lof in self.g['etfinit']:
                if get_rate_pri(lof[:6], self.g['days'],today,dates_open,prices) < -0.05 and lof[:6] in position:
                    print(lof + '跌幅高于5%，卖出')

                    price = prices[lof[:6]][today]
                    if sell(price, lof, balance, position):
                        print('成功卖出' + str(lof))
            if balance['可用金额'] > 0:
                for lof in self.g['etf']:
                    if lof == None:
                        continue
                    if get_rate_pri(lof[:6], self.g['days'],today,dates_open,prices) > 0.05 and lof[:6] not in position:
                        print(lof + '涨幅高于5%，买入')
                        price = prices[lof[:6]][today]
                        if buy(price, lof, balance, position, sub_value):
                            print('成功买入' + str(lof))
            # print('剩余现金：' + str(balance['可用金额']))
            print('最终账户信息为：')
            print(balance, position)
            return

        def do_market_2(balance,position,today,dates_open,prices):
            half_value = balance['总资产']
            print('Total value is: ' + str(half_value * 2))
            increase_rate = get_rate_pri(self.g['CYB'][:6], self.g['days'], today, dates_open, prices)
            if increase_rate > 0.07:
                print('创业板涨幅为' + str(increase_rate) + ',超过7%，以进攻策略持有创业板，空仓纳斯达克')
                if self.g['Nasdaq'][:6] in position:
                    price = prices[self.g['Nasdaq'][:6]][today]
                    if sell(price, self.g['Nasdaq'], balance, position):
                        print('成功卖出纳斯达克')
                if self.g['CYB'][:6] not in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if buy(price, self.g['CYB'], balance, position, half_value):
                        print('成功买入创业板')
            elif increase_rate < 0:
                print('创业板涨幅为' + str(increase_rate) + ',低于0%,以防守策略半仓纳斯达克，空仓创业板')
                if self.g['CYB'][:6] in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if sell(price, self.g['CYB'], balance, position):
                        print('成功卖出创业板')
            else:
                print('创业板涨幅为' + str(increase_rate) + ',高于0%，低于7%，持仓不动')
            if self.g['Nasdaq'][:6] not in position and self.g['CYB'][:6] not in position:
                price = prices[self.g['Nasdaq'][:6]][today]
                if buy(price, self.g['Nasdaq'], balance, position, half_value):
                    print('成功买入纳斯达克')
            # print('剩余现金：' + str(balance['可用金额']))
            print('最终账户信息为：')
            print(balance, position)
            return

        def get_fund(today, dates_open, prices):
            df_code_list = self.g['etfinit']
            stack = [-1 for i in range(self.g['length_candidate'])]
            re_lofs = [None for i in range(self.g['length_candidate'])]
            for lof in df_code_list:
                get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices)
                if get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices) > 0.3:
                    rate = get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices)
                    if rate > stack[-1]:
                        index = self.insert(stack, rate)
                        stack = stack[:index] + [rate] + stack[index:-1]
                        re_lofs = re_lofs[:index] + [lof] + re_lofs[index:-1]
            return re_lofs

        dates = dict()
        dates_open = []
        time_period = [start]
        benchmark_returns = []
        for lof in benchmark:
            benchmark_returns.append([0])
        for i in range(len(dates_vec)):
            dates[dates_vec[i]] = opens[i]
        for date in dates:
            if dates[date]==1:
                dates_open.append(date)
        for date in dates_open:
            if date<start:
                continue
            renew(account1.balance,account1.position,date,prices)
            renew(account2.balance, account2.position, date, prices)
            self.g['etf'] = get_fund(date, dates_open, prices)
            print(date)
            print(self.g['etf'])
            do_market(account1.balance,account1.position,date,dates_open,prices)
            do_market_2(account2.balance, account2.position, date, dates_open, prices)
            account1.values.append((account1.balance['总资产']-totalmoney)/totalmoney)
            account2.values.append((account2.balance['总资产'] - totalmoney) / totalmoney)
            account1.values_his.append(account1.balance['总资产'])
            account2.values_his.append(account2.balance['总资产'])
            time_period.append(date)
            for i,lof in enumerate(benchmark):
                if date in prices[lof[:6]]:
                    benchmark_returns[i].append((prices[lof[:6]][date] - prices[lof[:6]][start]) / prices[lof[:6]][start])
                else:
                    benchmark_returns[i].append(benchmark_returns[i][-1])
        #计算策略1胜率
        win_ = 0
        count_ = 0
        for i in range(1, len(account1.values_his)):
            if (account1.values_his[i] - account1.values_his[i - 1]) / account1.values_his[i - 1] > (
                    account2.values_his[i] - account2.values_his[i - 1]) / account2.values_his[i - 1]:
                win_ = win_ + 1
            count_ = count_ + 1
        print(
            'Winning rate of ' + account1.strategy_name + ' over ' + account2.strategy_name + ' is: ' + str(win_ / count_))

        win_ = 0
        count_ = 0
        for i in range(1, len(account1.values_his)):
            if 0 < (account2.values_his[i] - account2.values_his[i - 1]) / account2.values_his[i - 1]:
                win_ = win_ + 1
            count_ = count_ + 1
        print(
            'Winning rate of ' + account2.strategy_name + ' is: ' + str(
                win_ / count_))
        #绘图回测试结果
        time_period_new = [datetime.strptime(d, '%Y%m%d').date() for d in time_period]
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.xticks(time_period_new[::122])
        plt.ylabel("Return")
        plt.xlabel("Date")
        plt.plot(time_period_new, account1.values, label=account1.strategy_name)
        plt.plot(time_period_new, account2.values, label=account2.strategy_name)
        def compute_days(start, end):
            start = datetime.strptime(start, "%Y%m%d")
            end = datetime.strptime(end, "%Y%m%d")
            return int((end-start).days)
        diff_days = compute_days(start, end)
        print('Annualized return of %s is %s', account1.strategy_name, (account1.values_his[-1]/account1.values_his[0])**(365/diff_days) - 1)
        print('Annualized return of %s is %s', account2.strategy_name, (account2.values_his[-1]/account2.values_his[0])**(365/diff_days) - 1)
        for i,lof in enumerate(benchmark_returns):
            plt.plot(time_period_new, lof, label=benchmark[i])
        plt.legend()
        plt.gcf().autofmt_xdate()  # 自动旋转日期标记
        plt.grid()
        plt.show()
        return

    def run_once(self, start, end, totalmoney, params):
        print('本次尝试参数为')
        print(params)
        date_start = '20110101'
        dates_vec = list(self.pro.query('trade_cal', start_date=date_start, end_date=end)['cal_date'])
        opens = list(self.pro.query('trade_cal', start_date=date_start, end_date=end)['is_open'])
        account2 = Account(totalmoney, 'CYB—NASDAQ')
        prices = dict()
        for fund in self.g['etfinit']:
            prices[fund[:6]] = self.get_bar(fund, date_start, end)
        prices[self.g['Nasdaq'][:6]] = self.get_bar(self.g['Nasdaq'], date_start, end)
        prices[self.g['CYB'][:6]] = self.get_bar(self.g['CYB'], date_start, end)

        def get_rate_pri(fund, days, today, dates_open, prices):
            if fund == None:
                return -1
            index_today = dates_open.index(today)

            last_today = dates_open[index_today - days]

            if prices[fund][last_today] == 0:
                return -1
            rate = (prices[fund][today] - prices[fund][last_today]) / prices[fund][last_today]
            return rate

        def sell(price, stock_num, balance, position):
            if stock_num[:6] not in position:
                print('下单失败，' + stock_num + "不在持仓中")
                return False
            else:
                amount = position[stock_num[:6]]
                balance['可用金额'] = balance['可用金额'] + price * amount
                del position[stock_num[:6]]
                print('以' + str(price) + '卖出' + str(amount) + '份' + str(stock_num) + '增加' + str(amount * price) + '元')
                print('新账户信息为：')
                print(balance, position)
                return True

        def buy(price, stock_num, balance, position, total_money):
            amount = 100 * (total_money // (price * 100))
            if amount < 100:
                print("资金不足购买100股票，购买失败")
                return False
            if price * amount > balance['可用金额']:
                print('下单失败，可用金额小于下单金额，检查是否有订单堆积')
                return False
            position[stock_num[:6]] = amount
            balance['可用金额'] = balance['可用金额'] - price * amount
            print('以' + str(price) + '买入' + str(amount) + '份' + str(stock_num) + '花费' + str(amount * price) + '元')
            print('新账户信息为：')
            print(balance, position)
            return True

        def renew(balance, position, today, prices):
            totoal_value = 0
            for key in position:
                totoal_value = totoal_value + prices[key][today] * position[key]
            totoal_value = totoal_value + balance['可用金额']
            balance['总资产'] = totoal_value
            return

        def do_market_2(balance, position, today, dates_open, prices):
            half_value = balance['总资产']
            increase_rate = get_rate_pri(self.g['CYB'][:6], params['days'], today, dates_open, prices)
            if increase_rate > params['buy_th']:
                if self.g['Nasdaq'][:6] in position:
                    price = prices[self.g['Nasdaq'][:6]][today]
                    if sell(price, self.g['Nasdaq'], balance, position):
                        pass
                if self.g['CYB'][:6] not in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if buy(price, self.g['CYB'], balance, position, half_value):
                        pass
            elif increase_rate < params['sell_th']:
                if self.g['CYB'][:6] in position:
                    price = prices[self.g['CYB'][:6]][today]
                    if sell(price, self.g['CYB'], balance, position):
                        pass
            else:
                pass
            if self.g['Nasdaq'][:6] not in position and self.g['CYB'][:6] not in position:
                price = prices[self.g['Nasdaq'][:6]][today]
                if buy(price, self.g['Nasdaq'], balance, position, half_value):
                    pass
            return

        def get_fund(today, dates_open, prices):
            df_code_list = self.g['etfinit']
            stack = [-1 for i in range(self.g['length_candidate'])]
            re_lofs = [None for i in range(self.g['length_candidate'])]
            for lof in df_code_list:
                get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices)
                if get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices) > 0.3:
                    rate = get_rate_pri(lof[:6], self.g['days_filter'], today, dates_open, prices)
                    if rate > stack[-1]:
                        index = self.insert(stack, rate)
                        stack = stack[:index] + [rate] + stack[index:-1]
                        re_lofs = re_lofs[:index] + [lof] + re_lofs[index:-1]
            return re_lofs

        dates = dict()
        dates_open = []
        time_period = [start]
        for i in range(len(dates_vec)):
            dates[dates_vec[i]] = opens[i]
        for date in dates:
            if dates[date] == 1:
                dates_open.append(date)
        for date in dates_open:
            if date < start:
                continue
            renew(account2.balance, account2.position, date, prices)
            self.g['etf'] = get_fund(date, dates_open, prices)
            do_market_2(account2.balance, account2.position, date, dates_open, prices)
            account2.values.append((account2.balance['总资产'] - totalmoney) / totalmoney)
            account2.values_his.append(account2.balance['总资产'])
            time_period.append(date)

        return account2.values_his[-1]


    def object_func(self, trial):

        params = dict()
        params['buy_th'] = trial.suggest_float('buy_th', 0.0001, 0.2)
        params['sell_th'] = trial.suggest_float('sell_th', -0.2, 0)
        params['days'] = trial.suggest_int('days', 0, 60)
        final_value = self.run_once('20180104','20220825',500000, params)
        return final_value


    def run_strtegy_once(self, params):
        self.__init__()
        time.sleep(1)
        self.open_tonghuashun_exe()
        time.sleep(10)
        self.check_open()
        time.sleep(5)
        self.before_market()
        time.sleep(5)
        self.market(params)
        time.sleep(5)
        self.killexe()
        time.sleep(5)

    def run_params(self):
        self.back_testing('20180104', '20221117', 200000, ['513100.SH', '159915.SZ'])
        study = optuna.create_study(direction='maximize')
        study.optimize(self.object_func, n_trials=100)
        best_trial = study.best_trial
        print('best_params are: ')
        for key, value in best_trial.params.items():
            print('{}, {}'.format(key, value))





def main():
    #初始化参数
    print('自动交易程序运行中')
    params = dict()
    params['buy_th'] = 0.07105323899503448
    params['sell_th'] = -0.04008362549622712
    params['days'] = 16
    # autotrader = Autotrader()
    # # schedule.every().day.at("22:45").do(autotrader.run_strtegy_once, params)
    # # while True:
    # #     schedule.run_pending()
    #
    # autotrader.get_rate_close_only('159915.SZ', 20)
    # autotrader.run_strtegy_once()
    # autotrader = Autotrader()
    # autotrader.run_strtegy_once()
    # autotrader.run_strtegy_once()

    autotrader = Autotrader()

    autotrader.back_testing('20180104', '20221117', 200000, ['513100.SH', '159915.SZ'])
    study = optuna.create_study(direction='maximize')
    study.optimize(autotrader.object_func, n_trials=100)
    best_trial = study.best_trial
    print('best_params are: ')
    for key, value in best_trial.params.items():
        print('{}, {}'.format(key, value))
    schedule.every().day.at("08:54").do(autotrader.run_strtegy_once, best_trial.params)


if __name__ == "__main__":
    main()