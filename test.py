import backtest
import pandas as pd
import numpy as np
import pickle



'''
df_rt是我们要准备的收益率数据，
port_weights是一个dict，key是日期，value是Series（组合权重）
backtest_end_date是str,例如 '20200131' 代表回测到哪一日
costbuy是买入成本
costsell是卖出成本
DealPrice_DIY是bool，代表是否自己指定买卖价格
若 DealPrice_DIY是1，那么下面2个参数会被启用
sellprice是str，代表 df_rt的某一列的名字
buyprice是str，代表 df_rt的某一列的名字，卖出价

'''

'''逻辑
界面选择，先做单策略
1、单策略
2、指定 “策略时序权重文件”： port_weights 
3、指定 “回测结束日”：backtest_end_date
4、指定 “买入成本”：costbuy
5、指定卖出成本：costbuy
6、选择  “是否自行设定买卖价格":costbuy
7、若6为1，那么指定 
“卖出价格”: sellprice, 可选项目 '前收盘价':sellprice="pre_close",  “开盘价”：sellprice='open',
'均价': sellprice = 'Average', "收盘价"：sellprice = "close"

“买入价格”：buyprice 跟上面的选项一样
8、指定策略文件生成路径  file_OutPath
'''


with open("data//BackTest_DiliverOrder_NoIO.pkl", 'rb') as f:
    df_rt, port_weights, backtest_end_date, costbuy, costsell, DealPrice_DIY, sellprice, buyprice = pickle.load(f)
'''
流程1：回测生成组合日收益序列 并 生成相关excel底表
假设 数据已经找好，参数都设定好（用上面的with open语句完成）
'''

port_rt, port_Turnover = backtest.BackTest_DiliverOrder_NoIO(df_rt, port_weights, backtest_end_date, costbuy, costsell, DealPrice_DIY, sellprice, buyprice)
port_rt = pd.DataFrame(port_rt)
port_rt = port_rt.reset_index()
port_rt.columns = ['trade_date', 'rt']
port_Turnover = pd.DataFrame(port_Turnover)
port_Turnover = port_Turnover.reset_index()
port_Turnover.columns = ['trade_date', 'turnover']
port_rt.to_excel(f"file_OutPath//策略收益率序列.xlsx", index=False)
port_Turnover.to_excel(f"file_OutPath//策略换手率序列.xlsx", index=False)
# 先做个单策略回测的样例


'''
流程2：策略评价
'''
# 读入数据
port_rt = pd.read_excel(f"file_OutPath//策略收益率序列.xlsx")
port_rt.trade_date = pd.to_datetime(port_rt.trade_date.apply(str))
first_day = port_rt.trade_date.iloc[0]
first_day = first_day - backtest.Day(1)
# first_day = first_day.to_period("D")
# port_rt.trade_date = port_rt.trade_date.apply(lambda x:x.to_period('D'))
port_rt = port_rt.set_index('trade_date')
port_rt.loc[first_day] = 0
port_rt = port_rt.sort_index()

port_asset = (port_rt+1).cumprod()
data_performance = port_asset.apply(backtest.finance_report, axis=0)
# 生成表格
print(data_performance)














