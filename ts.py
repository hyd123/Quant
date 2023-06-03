
import tushare as ts


pro = ts.pro_api()
ts.set_token('2b33503f5c25fd8ddd78d2cc85827b7e6c8751dc9072bde2ab109214')
df = pro.fund_daily(ts_code='159915.SZ')
print(df)