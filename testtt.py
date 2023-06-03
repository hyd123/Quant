import akshare as ak
import pandas as pd
import optuna
import time
import smtplib
import schedule
from email.mime.text import MIMEText
from matplotlib import pyplot as plt

class Autotrader:
    def __init__(self):
        self.g = dict()
        self.unit = 3600 * 24
        self.before_market_time = 9
        self.market_time = 10
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

    def get_rate(self, fund, days, sdate, edate):
        if fund == None:
            return -1
        # df = self.pro.fund_daily(ts_code=fund)
        df = ak.fund_etf_hist_em(symbol=fund, start_date=sdate, end_date=edate, adjust='qfq')
        close_data = list(df['收盘'])[-days - 1:]
        if len(close_data) < days:
            return -1
        rate = (close_data[-1] / close_data[0] - 1)
        return rate

    def check_buy_sell(self):
        date = time.strftime("%Y%m%d", time.localtime())
        rate = self.get_rate('159915', 20, '20220101', date)
        if rate > 0.07:
            trade_info = '卖出纳斯达克，买入创业板'
        elif rate < 0:
            trade_info = '卖出创业板，买入纳斯达克'
        else:
            trade_info = '持仓不动'
        information = '日期为：' + time.strftime("%Y-%m-%d", time.localtime()) + ', 创业板涨幅为: ' + str(rate) + '.' + trade_info
        self.send_email(information)

    def send_email(self, content):
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



# study = optuna.create_study(direction='maximize')
# study.optimize(object_func, n_trials=100)
# best_trial = study.best_trial
# print('best_params are: ')
# for key, value in best_trial.params.items():
#     print('{}, {}'.format(key, value))

def main():
    #初始化参数
    print('自动交易程序运行中')
    params = dict()
    params['buy_th'] = 0.07105323899503448
    params['sell_th'] = -0.04008362549622712
    params['days'] = 16
    at = Autotrader()
    schedule.every().day.at("08:54").do(at.check_buy_sell)
    while True:
        schedule.run_pending()




if __name__ == "__main__":
    main()


at = Autotrader()
at.check_buy_sell()