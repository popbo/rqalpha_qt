from rqalpha.api import *
import talib
import pandas as pd


def get_kdj_pd(stock, n=9,m1 = 2, m2 = 2,ksgn='close'):
    nd = history_bars(stock, n+10, '1d')
    df = pd.DataFrame(nd, columns=["datetime", "open", "high", "low", "close", "volume"])
    lowList = df['low'].rolling(n).min() #计算low值9日移动最低
    lowList.fillna(value=df['low'].expanding().min(), inplace=True)
    highList = df['high'].rolling(n).max() #计算high值9日移动最高
    highList.fillna(value=df['high'].expanding().max(), inplace=True)
    rsv = (df.loc[:, 'close'] - lowList) / (highList - lowList) * 100
    df.loc[:, 'kdj_k'] = rsv.ewm(com=m1-1).mean()
    df.loc[:, 'kdj_d'] = df.loc[:, 'kdj_k'].ewm(com=m2-1).mean()
    df.loc[:, 'kdj_j'] = 3.0 * df.loc[:, 'kdj_k'] - 2.0 * df.loc[:, 'kdj_d']
    return df['kdj_k'].tolist(), df['kdj_d'].tolist()


def get_kd_ta(stock, n=9,m1 = 3, m2 = 3):
    p=100
    hhigh = history_bars(stock, p, '1d', 'high')
    hlow = history_bars(stock, p, '1d', 'low')
    hclose = history_bars(stock, p, '1d', 'close')
    talib_K, talib_D = talib.STOCH(hhigh,
                                   hlow,
                                   hclose,
                                   fastk_period=n,
                                   slowk_period=2*m1-1,
                                   slowk_matype=1,
                                   slowd_period=2*m2-1,
                                   slowd_matype=1)#计算kdj的正确配置
 
    talib_J = 3.0 * talib_K - 2.0 * talib_D

    return talib_K, talib_D


def get_trade_flag_value(list_k, list_d):
    slowk = list_k[-1]
    slowd = list_d[-1]
    if slowk > 90 or slowd > 90:
        return -1
    # 当slowk < 10 or slowd < 10, 且拥有的股票数量<=0时，则全仓买入
    elif slowk < 10 or slowd < 10:
        return 1
    return 0

def get_trade_flag_cross(list_k, list_d):
    if len(list_k) < 2:
        return 0
    if list_k[-1] > list_d[-1] and list_k[-2] <= list_d[-2]:
        return 1
    elif list_k[-1] <= list_d[-1] and list_k[-2] > list_d[-2]:
        return -1
    return 0

def calc_trade_flag(pfKdj, pfFlag, stock, config):
    list_k, list_d = pfKdj(stock, config.N, config.M1, config.M2)
    return pfFlag(list_k, list_d)


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def init(context):
    # logger.info("init")
    #update_universe(context.s1)
    context.stocks = context.config.stocks

def before_trading(context):
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 取得当前的现金
    cash = context.portfolio.cash
    list_trade_flag=[]

    # 循环股票列表
    for stock in context.stocks:
        trade_flag=calc_trade_flag(get_kd_ta, get_trade_flag_cross, stock, context.config.paras)
        list_trade_flag.append(trade_flag)

    buy_list=[]
    sell_list=[]
    for i in range(len(context.stocks)):
        if list_trade_flag[i] > 0:
            buy_list.append(context.stocks[i])
        elif list_trade_flag[i] < 0:
            sell_list.append(context.stocks[i])

    for stock in sell_list:
        # 获取当前股票的数据
        current_position = context.portfolio.positions[stock].quantity
        if current_position > 0:
            order_target_percent(stock, 0)

    n=len(buy_list)
    for stock in buy_list:
        order_target_percent(stock, 1/n)

def append_indicator_draw(df, config,add_plot):
    import mplfinance as mpf
    talib_K, talib_D = talib.STOCH(df['high'],
                                df['low'],
                                df['close'],
                                fastk_period=config['paras']['N'],
                                slowk_period=2*config['paras']['M1']-1,
                                slowk_matype=1,
                                slowd_period=2*config['paras']['M2']-1,
                                slowd_matype=1)#计算kdj的正确配置
    add_plot.append(mpf.make_addplot(talib_K,panel=2,color='blue'))
    add_plot.append(mpf.make_addplot(talib_D,panel=2,color='red'))