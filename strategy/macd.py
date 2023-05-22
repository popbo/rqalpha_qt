from rqalpha.api import *
import talib
import pandas as pd


def get_macd_pd(stock, n=9,m1 = 2, m2 = 2,ksgn='close'):
    pass


def get_macd_ta(stock, SHORT=12,LONG = 26, SMOOTH = 9):
    hclose = history_bars(stock, 100, '1d', 'close')
    macd, signal, hist = talib.MACD(hclose, SHORT, LONG, SMOOTH)

    return macd, signal, hist

def get_trade_flag_cross(macd, signal, hist):
    if len(macd) < 2:
        return 0
    if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
        return 1
    elif macd[-1] <= signal[-1] and macd[-2] > signal[-2]:
        return -1
    return 0

def calc_trade_flag(pfCalc, pfFlag, stock, config):
    macd, signal, hist = pfCalc(stock, config.SHORT, config.LONG, config.SMOOTH)
    return pfFlag(macd, signal, hist)


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
        trade_flag=calc_trade_flag(get_macd_ta, get_trade_flag_cross, stock, context.config.paras)
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
    macd, signal, hist = talib.MACD(df['close'], config['paras']['SHORT'], config['paras']['LONG'],config['paras'] ['SMOOTH'])
    df['macd']=macd
    df['signal']=signal
    add_plot.append(mpf.make_addplot(macd,panel=2,color='blue'))
    add_plot.append(mpf.make_addplot(signal,panel=2,color='red'))
    return df