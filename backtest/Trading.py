import numpy as np
import pandas as pd
from dateutil.parser import parse
from pandas.tseries.offsets import Day,MonthEnd
import datetime

fun_date_tosimple = lambda x:f"{x[0:4]}{x[5:7]}{x[8:10]}"
fun_date_tocomplex = lambda x:f"{x[0:4]}-{x[4:6]}-{x[6:8]}"
fun_date_simpletowind = lambda x:f"{x[0:4]}/{int(x[4:6])}/{int(x[6:8])}"
'''
1、calculate_turnover(old_holding, new_holding) 计算从旧组合到新组合的换手率
2、BackTest_DiliverOrder_NoIO(Daily, DiliverOrder_dict, enddate, costbuy=0.001, costsell=0.002, DealPrice_DIY=False, sellprice='Nan', buyprice="Nan")
    传入日线数据，传入每个交易日的权重表，获得组合每个交易日的收益
'''

'''1、传入2个归一化的组合，计算换手率'''
# old_holding, new_holding = last_portfolio, now_portfolio
def calculate_turnover(old_holding, new_holding):
    '''
    :param old_holding: dict or
    :param new_holding: dict or
    :return:
    turnover, df_gap
    turnover ： 0.6
    df_gap：
        000012.SZ        0.4
        万科A           -0.4
        中国平安        -0.2
        古井贡酒         0.2

    逻辑：
    组合权重想减，取绝对值，加和除以2就是换手率，一般来说这个换手率乘以双边千3就是成本
    本函数还会返回一个买卖方向的dataframe
    1、np.nan会被当成是0(fillna)
    2、输入必须是一个组合，加权为1
    3、如果有现金账户，那么这个turnover的返回就是错的，得利用df_gap重新算
    '''
    '''
    Test Example for 'dict' input:
    old_holding = {'中国平安':0.2, '000012.SZ':0.4, '万科A':0.4}
    new_holding= {'古井贡酒':0.2, '000012.SZ':0.8, '万科A':np.nan}
    
    Test Example for 'Series' input:
    old_holding = pd.Series({'中国平安':0.2, '000012.SZ':0.4, '万科A':0.4})
    new_holding= pd.Series({'古井贡酒':0.2, '000012.SZ':0.8, '万科A':np.nan})
    
    Test Example for 'Series' input:
    old_holding = pd.DataFrame(pd.Series({'中国平安':0.2, '000012.SZ':0.4, '万科A':0.4}))
    new_holding= pd.DataFrame(pd.Series({'古井贡酒':0.2, '000012.SZ':0.8, '万科A':np.nan}))
    old_holding = old_holding.reset_index()
    old_holding.columns = ['whatever1', 'whatever2']
    new_holding = new_holding.reset_index()
    new_holding.columns = ['whatever1', 'whatever2']
    '''
    if isinstance(old_holding, dict):
        df_old_holding = pd.DataFrame(pd.Series(old_holding))
        df_old_holding.columns = ['old']
        df_new_holding = pd.DataFrame(pd.Series(new_holding))
        df_new_holding.columns = ['new']
    elif isinstance(old_holding, pd.core.series.Series):
        df_old_holding = pd.DataFrame(old_holding)
        df_old_holding.columns = ['old']
        df_new_holding = pd.DataFrame(new_holding)
        df_new_holding.columns = ['new']
    elif isinstance(old_holding, pd.core.frame.DataFrame):
        if old_holding.shape[1] == 2:   # 有2列，默认第一列是资产名字
            cols = list(old_holding.columns)
            df_old_holding = old_holding.set_index(cols[0])
            df_new_holding = new_holding.set_index(cols[0])
        df_old_holding.columns = ['old']
        df_new_holding.columns = ['new']
    else:
        raise ValueError("calculate_turnover函数的输入必须是 dict、Series、DataFrame的一种")

    df = pd.merge(df_old_holding, df_new_holding, left_index=True, right_index=True, how='outer')
    df = df.fillna(0)


    '''判断组合权重有没有问题'''
    dfsum = df.sum()
    if (dfsum > 1.001).sum() > 0 or (dfsum < 0.999).sum() > 0:
        raise ValueError("组合权重之和不满足等于1的条件，请检查calculate_turnover的输入")

    df_gap = df.new - df.old

    turnover = df_gap.abs().sum() / 2   # 比如0.6，代表百分之60的资金参与了买入和卖出
                                        # 如果涉及到现金的话，还是用返回的df_gap再另算吧

    return turnover, df_gap
#
# Daily = df_rt.copy()
# DiliverOrder_dict = Ave_Portfolio_TimeSeries.copy()
# enddate = '20200101'
# costbuy=0.001
# costsell=0.002
# DealPrice_DIY=True
# sellprice='S_DQ_ADJAVGPRICE'
# buyprice="S_DQ_ADJAVGPRICE"

'''2、传入日线数据，传入历史上各个交易日的权重表，获得历史上组合每个交易日的收益'''
# Daily, DiliverOrder_dict, enddate = df_rt, port_weights, backtest_end_date
# costbuy=0.001
# costsell=0.002
# DealPrice_DIY=True
# sellprice='open'
# buyprice="open"
def BackTest_DiliverOrder_NoIO(Daily, DiliverOrder_dict, enddate, costbuy=0.001, costsell=0.002, DealPrice_DIY=False, sellprice='Nan', buyprice="Nan"):
    '''
    注意：
    这个函数不会去判断每一期的股票到底能不能买入;
    Daily需要有几列存在
    若要有现金账户，也可，但要传入现金对应的收益率，现金的各类价格都是1

    :param Daily: dataframe
    ts_code：代码
    pct_chg：小数收益率
    trade_date：str,object：20071214
    如果DealPrice_DIY==True,更进一步需要下面的列，注意下面的是复权价
    open：复权开盘价
    close：复权收盘价
    pre_close：前复权收盘价

    :param DiliverOrder_dict: key是交易日，value是目标权重
    是Series的形式，index是资产名字，value是归一化的权重

    :param enddate: 最后一期看到哪 str  20200106
    :param DealPrice_DIY: bool，是否采用复杂的交易模式，默认为False
    False状态下： 昨日收盘价卖出，昨日收盘价买入
    比如第一期是20191108，那么默认20191107收盘价买入了股票，所以20191108整天的收益都能吃到
    20191206换仓时候，假设20191205收盘价换仓完毕，都以收盘价成交
    True状态下：采用指定价格进行买入和卖出

    :param costbuy: 买入时候的成本，默认为千1
    :param costsell: 卖出的成本，默认为千3
    :param buyprice: str，必须在Daily中有这一列
    :param sellprice： str，必须在Daily中有这一列
    sellprice='vwap', buyprice="vwap"必须指定。譬如:
    代表以当日的vwap卖出，以当日的vwap买入
    事实上，以什么价格买入卖出只影响收益，不影响换手率的计算
    若都是vwap，
    那么代表当日以均价买入，那么以前的组合的收益还要计算，vwap

    Daily.columns
    costbuy = 0.001
    costsell = 0.002
    enddate = 20100401
    DealPrice_DIY = False
    buyprice = 'open'
    sellprice = 'pre_close'
    # 上面这两个组合代表的是，今天的组合，在昨天用收盘价全卖了，今天的组合用开盘价买进来了
    import pickle
    with open("BackTest_DiliverOrder_NoIO.pkl", 'rb') as f:
        df_rt, port_weights, backtest_end_date, costbuy, costsell, DealPrice_DIY, sellprice, buyprice = pickle.load(f)

    :return:
    '''

    '''确保日线数据有相关的列'''
    if DealPrice_DIY:
        Daily_cols = list(Daily.columns)
        assert all([x in Daily_cols for x in ['ts_code', 'pct_chg', 'trade_date', 'open', 'close', 'pre_close', buyprice, sellprice]])
    else:
        Daily_cols = list(Daily.columns)
        # assert all([x in Daily_cols for x in ['ts_code', 'pct_chg', 'trade_date', 'open', 'close', 'pre_close']])
        assert all([x in Daily_cols for x in ['ts_code', 'pct_chg', 'trade_date']])

    '''确保Daily的pct_chg是小数收益率'''
    assert all(Daily.pct_chg > -1)


    all_trade_dates = Daily.trade_date.unique() # 在日线行情数据里面涉及的交易日, 用来查看2个diliver_date相差多少个交易日

    '''用来记录组合的收益率'''
    portfolio_rt_record = pd.Series()  # 用来记录组合的收益率, 注意1%的收益率在这里是1.01

    '''用来记录组合的换手率'''
    portfolio_turnover_record = pd.Series()


    all_diliver_dates = DiliverOrder_dict.keys()    # 所有的 weight
    all_diliver_dates = sorted(all_diliver_dates)


    if DealPrice_DIY:
        '''自己设定买卖价格
        这个跟 DealPrice_DIY==False 的区别在于：
        DealPrice_DIY=False时，调仓日昨天收盘调仓完毕，所以今天的收益是全包括的
        DealPrice_DIY=True时，调仓当日要细致处理
        一般来说，如果daily上面有pre_close，那么，指定 buyprice='pre_close'和sellprice='pre_close'跟不指定DIY是一样的
        '''
        all_loop_date = all_diliver_dates + [enddate]  # 把最后一个enddate也放进去
        N = len(all_loop_date)

        i = 0
        for i in range(N - 1):  # 对每一个换仓日进行循环，不包括enddate
            now_date = all_loop_date[i]

            '''这个if-elif-else语句用来考虑调仓当天的收益率'''
            if i == 0:  # 因为函数默认以昨日收盘价进行处理，因此今天的收益是考虑了买入手续费和当日整日收益率的
                last_portfolio = DiliverOrder_dict[now_date]  # 取得第一期的组合
                last_portfolio = last_portfolio[last_portfolio != 0]
                portfolio_turnover_record[str(now_date)] = 1

                '''加入换手率成本'''
                rt_huancang = 1 - costbuy  # 换手成本

                all_portcode = np.array(last_portfolio.index)
                Daily_temp = Daily[Daily.ts_code.isin(all_portcode) & (Daily.trade_date==now_date)].copy() # 当日的收益率

                """用上一次的portfolio来计算净值变动"""
                Daily_temp['new_rt'] = Daily_temp.close / Daily_temp[buyprice]   # 计算买入后，到收盘的收益率
                Daily_temp = pd.pivot_table(Daily_temp, columns='ts_code', index='trade_date', values='new_rt')
                Daily_temp = Daily_temp.fillna(0)
                try:
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                except:   # 没有数据用0补全
                    code_have_data = list(Daily_temp.columns)
                    miss_codes = [x for x in all_portcode if x not in code_have_data]
                    for code_temp in miss_codes:
                        Daily_temp[code_temp] = 0
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                    Daily_temp = (Daily_temp + 1).cumprod()

                Asset_temp = Daily_temp * last_portfolio   # 经过今天后，组合内每一个资产的asset


                portfolio_rt_record[now_date] = Asset_temp.sum(axis=1).iloc[0] * rt_huancang - 1 # 考虑了买入成本的当天收入

                last_portfolio = Asset_temp.T.iloc[:,0].copy()
                last_portfolio = last_portfolio / last_portfolio.sum()  # 归一化的组合
            else:  # 非第一日，但这里面不包括组合到最后一日
                '''
                先卖，后买，因为在这种状态下，是有原来的持仓的。
                last_portfolio在传入这个else的时候，已经考虑了过去的持仓的收益，导致的组合权重的变动
                顺序：
                第一步：先考虑今天至卖出前的持有收益率，归一化组合
                第二步：取出新的组合，计算换手率，记录下换手成本收益
                第三步：第一步归一化的组合来计算，今天买入的组合持有到收盘的收益率，last_portfolio=now_portfolio      
                '''

                '''-------------第一步：计算原组合至卖出的收益率, last_portfolio已经在最下面的ifelse被归一化'''
                all_portcode = np.array(last_portfolio.index)
                Daily_temp = Daily[Daily.ts_code.isin(all_portcode) & (Daily.trade_date==now_date)].copy() # 当日的收益率

                """用上一次的portfolio来计算净值变动，sell_price/pre_close"""
                Daily_temp['new_rt'] = Daily_temp[sellprice] / Daily_temp['pre_close']   # 计算买入后，到收盘的收益率,+1的收益
                Daily_temp = pd.pivot_table(Daily_temp, columns='ts_code', index='trade_date', values='new_rt')
                Daily_temp = Daily_temp.fillna(1)
                try:
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(1)
                except: # 没有数据用0补全
                    code_have_data = list(Daily_temp.columns)
                    miss_codes = [x for x in all_portcode if x not in code_have_data]
                    for code_temp in miss_codes:
                        Daily_temp[code_temp] = 1
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(1)

                Asset_temp = Daily_temp * last_portfolio   # 经过今天后，组合内每一个资产的asset

                sell_rt = Asset_temp.sum(axis=1).iloc[0]   # 持有到卖出现有组合的收益率， part 1

                last_portfolio = Asset_temp.T.iloc[:,0].copy()
                last_portfolio = last_portfolio / last_portfolio.sum()  # 归一化的组合
                '''------------第一步:计算原组合至卖出的收益率（完毕）'''


                '''--------------第二步：计算换手的成本'''
                now_portfolio = DiliverOrder_dict[now_date]  # 取得第一期的组合
                now_portfolio = now_portfolio[now_portfolio != 0]
                tov, _ = calculate_turnover(last_portfolio, now_portfolio)

                portfolio_turnover_record[str(now_date)] = tov

                turnover_rt = 1 - tov * ( costbuy + costsell)   # 换手的收益率
                '''--------------第二步：计算换手的成本（完毕)'''


                '''-------------第三步：计算新组合买入后持有到收盘的收益率, last_portfolio已经在最下面的ifelse被归一化'''
                all_portcode = np.array(now_portfolio.index)  # 现在的组合
                Daily_temp = Daily[Daily.ts_code.isin(all_portcode) & (Daily.trade_date==now_date)].copy() # 当日的收益率

                """用上一次的portfolio来计算净值变动，sell_price/pre_close"""
                Daily_temp['new_rt'] = Daily_temp.close / Daily_temp[buyprice]    # 计算买入后，到收盘的收益率
                Daily_temp = pd.pivot_table(Daily_temp, columns='ts_code', index='trade_date', values='new_rt')
                Daily_temp = Daily_temp.fillna(1)
                try:
                    Daily_temp = Daily_temp[all_portcode]   # 按顺序
                    Daily_temp = Daily_temp.fillna(1)
                except: # 没有数据用0补全
                    code_have_data = list(Daily_temp.columns)
                    miss_codes = [x for x in all_portcode if x not in code_have_data]
                    for code_temp in miss_codes:
                        Daily_temp[code_temp] = 1
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(1)

                Asset_temp = Daily_temp * now_portfolio   # 现在的组合

                buy_rt = Asset_temp.sum(axis=1).iloc[0]   # 持有到卖出现有组合的收益率， part 1

                last_portfolio = Asset_temp.T.iloc[:,0].copy()
                last_portfolio = last_portfolio / last_portfolio.sum()  # 归一化的组合
                '''-----------第三步：计算新组合买入后持有到收盘的收益率（完毕）'''


                portfolio_rt_record[now_date] = buy_rt * sell_rt * turnover_rt - 1

            '''这边这个if-else语句用来考虑 今天这个调仓日 到 下一个调仓日（不含）之间的收益率'''
            next_date = str(all_loop_date[i + 1])  #
            '''注意DealPrice_DIY=True时
            是不！包含本日的，因为本日的收益率已经算进去了
            '''
            interval_trade_date = all_trade_dates[(all_trade_dates > now_date) & (all_trade_dates < next_date)]
            N_interval = len(interval_trade_date)
            if N_interval == 0:  # 如果中间没有任何交易日，那么跳过
                pass
            else:  # 中间有交易日的话，开始算
                all_portcode = np.array(last_portfolio.index)
                Daily_temp = Daily[Daily.ts_code.isin(all_portcode) & Daily.trade_date.isin(interval_trade_date)].copy()

                """用上一次的portfolio来计算净值变动"""
                Daily_temp = pd.pivot_table(Daily_temp, columns='ts_code', index='trade_date', values='pct_chg')

                try:
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                    Daily_temp = (Daily_temp + 1).cumprod()
                except:
                    code_have_data = list(Daily_temp.columns)
                    miss_codes = [x for x in all_portcode if x not in code_have_data]
                    for code_temp in miss_codes:
                        Daily_temp[code_temp] = 0
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                    Daily_temp = (Daily_temp + 1).cumprod()

                port_asset = Daily_temp * last_portfolio  # 注意这个last_portfolio是和为1的相对权重。
                port_asset_sum = port_asset.sum(axis=1)
                port_rt = port_asset_sum.pct_change()
                port_rt.iloc[0] = port_asset_sum.iloc[0] - 1  # 这边跟DIY=False不一样，不需要考虑换手

                portfolio_rt_record = pd.concat([portfolio_rt_record, port_rt], axis=0)

                '''!!!很重要，生成新的last_portfolio'''
                last_portfolio = port_asset.iloc[-1]
                last_portfolio = last_portfolio / last_portfolio.sum()  # 然后转到下一个调仓日，用来计算换手率
    else:    # 直接以昨日收盘价进行结算
        '''
        从第二个diliver_date开始，都要往前看之前的收益率
        '''
        all_loop_date = all_diliver_dates + [enddate]  # 把最后一个enddate也放进去
        N = len(all_loop_date)

        i = 0
        for i in range(N-1):   # 对每一个换仓日进行循环，不包括enddate
            now_date = all_loop_date[i]

            '''这个if-elif-else语句用来考虑调仓当天的收益率'''
            if i == 0:   # 因为函数默认以昨日收盘价进行处理，因此今天的收益是考虑了买入手续费和当日整日收益率的
                last_portfolio = DiliverOrder_dict[now_date]   # 取得第一期的组合
                last_portfolio = last_portfolio[last_portfolio!=0]

                portfolio_turnover_record[str(now_date)] = 1
                '''加入换手率'''
                rt_huancang = 1-costbuy

                '''不需要对portfolio进行调整，因为以同比例下调净值不影响相对权重，后面计算组合收益率也是用相对权重
                如果加了这句话，那么 port_rt.iloc[0] = port_asset.iloc[0] - 1 这句话就会出问题，因为起始组合之和不是1了
                '''
                # last_portfolio = last_portfolio * (1-costbuy)

            else:   # 非第一日，但这里面不包括组合到最后一日
                '''在这个情况下，新组合默认是昨天晚上调仓完毕
                所以，今天的收益包括了全天的收益
                步骤：
                1、昨天晚上全部卖出，先计算换手率，然后用双边的换手率计算成本(理论上成本应该是归结到昨天）
                但这边粗糙一点归结到当天吧。                
                '''
                now_portfolio = DiliverOrder_dict[now_date]   # 取得第一期的组合
                now_portfolio = now_portfolio[now_portfolio!=0]
                tov, _ = calculate_turnover(last_portfolio, now_portfolio)

                rt_huancang = 1 - tov * (costbuy + costsell)   # 换手成本

                last_portfolio = now_portfolio.copy()   # 调整

                portfolio_turnover_record[str(now_date)] = tov



            '''这边这个if-else语句用来考虑 今天这个调仓日 到 下一个调仓日（不含）之间的收益率'''
            next_date = str(all_loop_date[i+1])   #
            '''注意是包含本日的，换手成本是在前面rt_huancang考虑的'''
            interval_trade_date = all_trade_dates[(all_trade_dates>=now_date) & (all_trade_dates<next_date)]
            N_interval = len(interval_trade_date)
            if N_interval==0:   # 如果中间没有任何交易日，那么跳过
                pass
            else:   # 中间有交易日的话，开始算
                all_portcode = np.array(last_portfolio.index)
                Daily_temp = Daily[Daily.ts_code.isin(all_portcode) & Daily.trade_date.isin(interval_trade_date)].copy()

                """用上一次的portfolio来计算净值变动"""
                Daily_temp = pd.pivot_table(Daily_temp, columns='ts_code', index='trade_date', values='pct_chg')

                try:
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                    Daily_temp = (Daily_temp + 1).cumprod()
                except:
                    code_have_data = list(Daily_temp.columns)
                    miss_codes = [x for x in all_portcode if x not in code_have_data]
                    for code_temp in miss_codes:
                        Daily_temp[code_temp] = 0
                    Daily_temp = Daily_temp[all_portcode]
                    Daily_temp = Daily_temp.fillna(0)
                    Daily_temp = (Daily_temp + 1).cumprod()

                port_asset = Daily_temp * last_portfolio  # 注意这个last_portfolio是和为1的相对权重。
                port_asset_sum = port_asset.sum(axis=1)
                port_rt = port_asset_sum.pct_change()
                port_rt.iloc[0] = rt_huancang * port_asset_sum.iloc[0] - 1  # 昨日换仓的成本放在了今天

                portfolio_rt_record = pd.concat([portfolio_rt_record, port_rt], axis=0)


                '''!!!很重要，生成新的last_portfolio'''
                last_portfolio = port_asset.iloc[-1]
                last_portfolio = last_portfolio / last_portfolio.sum()  # 然后转到下一个调仓日，用来计算换手率

    return portfolio_rt_record, portfolio_turnover_record


