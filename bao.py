import baostock as bs
import pandas as pd#### 登陆系统 ####
lg = bs.login()
rs = bs.query_history_k_data_plus("sh.513100",
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
    start_date='2023-03-17', end_date='2023-03-28',
    frequency="d", adjustflag="2")

data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)
print(result)