import easyquotation

quotation = easyquotation.use('sina') # 新浪 ['sina'] 腾讯 ['tencent', 'qq']

#获取所有股票行情
quotation.market_snapshot(prefix=True) # prefix 参数指定返回的行情字典中的股票代码 key 是否带 sz/sh 前缀

#单只股票
print(quotation.real('162411')) # 支持直接指定前缀，如 'sh000001'

#多只股票
quotation.stocks(['000001', '162411'])

#同时获取指数和行情
print(quotation.stocks(['sh513100', 'sz159915'], prefix=True))

