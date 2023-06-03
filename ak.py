import akshare as ak
import pandas as pd

# 获取股票数据    fund_etf_hist_sina,
etf = ak.fund_etf_hist_em(symbol="513100")
print(etf)
