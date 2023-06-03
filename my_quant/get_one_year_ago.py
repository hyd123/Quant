import time



def get_two_year(date):
    timeArray = time.strptime(date, "%Y%m%d")
    timeStamp = (time.mktime(timeArray))  # 转化为时间戳
    start_year = int(time.strftime('%Y', time.localtime(timeStamp))) - 2
    month_day = time.strftime('%m%d', time.localtime(timeStamp))
    start_time = '{}{}'.format(start_year, month_day)
    return start_time

