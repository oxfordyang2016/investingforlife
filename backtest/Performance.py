'''
此模块用来作组合评价
'''
'''
函数记录
1、最大回撤              MaxDown(asset)     输入净值序列，计算最大回撤
2、给Series增加序列      add_period(x, value, date)     
3、计算单一组合表现      finance_report(x)       输入净值序列，计算单一组合指标
'''
import numpy as np
import pandas as pd
import datetime

'''1、输入净值序列，计算最大回撤'''
def MaxDown(asset):
    '''
    :param x:  净值序列  , np.nan值会用前值填充
    :return:
    '''
    # 例子：
    # import pandas as pd
    # import numpy as np
    # import time
    # x = pd.Series(np.random.rand(100), index=pd.date_range('20190810', periods=100))
    # x.iloc[10] = np.nan
    # start = time.clock()
    # for j in range(1000):
    #     new_MaxDown(x)  # (-0.9997405997634019, '2019-08-19', '2019-08-25')
    # elapsed = (time.clock() - start)
    # elapsed  # 0.19048577524881694
    if min(asset) <= 0:
        raise ValueError('净值序列包含小于等于0的数')
    x = list(asset.fillna(method='ffill'))
    j = np.argmin(x / np.maximum.accumulate(x) - 1)

    # i = np.argmax(x[:j])
    i = x[:j].index(max(x[:j]))
    d = x[j] / x[i] - 1

    return d, str(asset.index[i].date()), str(asset.index[j].date())


'''2、给序列增加数据'''
def add_period(x, value, date):
    '''
    :param x:  时间序列
    x = pd.Series([0.02, -0.014, -0.01, 0.11, 0.02, 0.006],index = pd.date_range('2011/01/31',periods=6,freq='M'))
    2011-01-31 00:00:00    0.020
    2011-02-28 00:00:00   -0.014
    2011-03-31 00:00:00   -0.010
    :param date: 要加上的value对应的index，str格式
    :param value: 要加上的value
    :return:
    使用方法：
    add_period(x,0,'2011-01-31')
    '''
    from dateutil.parser import parse
    if isinstance(x, pd.core.frame.DataFrame):
        x.loc[parse(date),:] = value
        x.sort_index(inplace=True)
    else:    # 如果是Series
        x[parse(date)] = value
        x.sort_index(inplace=True)
    return(x)


'''3、输入净值序列，计算单一组合指标'''
def finance_report(x):
    '''
    :param x: x是净值series,index是datetime数据,月度日度无所谓
    2014-01-31    1.000000
    2014-02-28    0.963437
    2014-03-31    0.920766
    2014-04-30    0.922582
    2014-05-31    0.909376
    :return:

    由于x是净值数据，当你原来有的是收益率数据的时候，如果你把收益率变成净值，是要在第一行加一行净值数据的，全是1
    建议你在这种情况下配合 add_period 函数使用:
    x = pd.Series([0.02, -0.014, -0.01, 0.11, 0.02, 0.006],index = pd.date_range('2011/01/31',periods=6,freq='M'))
    x = add_period(x,0,'2010/12/31')
    x = (x+1).cumprod()
    finance_report(x)
    '''
    x_pct = x.pct_change()
    x_pct = x_pct.dropna()

    sd = x_pct.std()
    mean = x_pct.mean()
    sharpe = mean / sd

    max_down, beg_date, end_date = MaxDown(x)

    mean_by_maxdown = -(mean / max_down)

    # 计算整个区间收益和年化收益
    # 先计算时间：
    interval_beg = str(datetime.datetime.date(x_pct.index[0]))
    interval_end = str(datetime.datetime.date(x_pct.index[-1]))
    intervals = (x_pct.index[-1] - x_pct.index[0]).days
    intervals = round(intervals / 365, 2)
    intervals_return = x.iloc[-1] / x.iloc[0] - 1
    intervals_yearlyreturn = (intervals_return + 1) ** (1 / intervals) - 1

    return (pd.Series(
        [interval_beg, interval_end, intervals, mean, sd, sharpe, intervals_return, intervals_yearlyreturn, max_down,
         mean_by_maxdown, beg_date, end_date],
        index=['起始日', '结束日', '区间长度(年)', '均值收益', '标准差', '夏普', '区间收益', '年化收益',
               '最大回撤', '均值/最大回撤', '最大回撤开始区间', '最大回撤结束区间']))



def test():
    print("----test function is here-----")