# run_file_demo
from rqalpha import run_file
import yaml

strategy='kdj'

f = open(f'./config/single/{strategy}.yml', 'r', encoding='utf-8')

config = {
  "base": {
    "data_bundle_path": "bundle/bundle",
    "start_date": "2022-01-01",
    "end_date": "2023-01-01",
    "benchmark": "000001.XSHE",
    "frequency": "1d",
    "accounts": {
      "stock": 100000
    }
  },
  "extra": {
    "log_level": "verbose",
  }, 
  "mod": {
    "sys_analyser": {
      "enabled": True,
      "plot": True,
    }
  },
  "stocks": ["000001.XSHE"],
  "paras":yaml.safe_load(f.read())
}

ret = run_file(f'./strategy/{strategy}.py', config)
print(ret['sys_analyser']['summary']['total_returns'])
ret['sys_analyser']['trades'].to_csv('./hrdata_modified.csv')

def draw_indicator():
  import mplfinance as mpf
  import pandas as pd
  import numpy as np
  import talib
  import importlib

  start = int(config['base']['start_date'].replace('-',''))*1000000
  end = int(config['base']['end_date'].replace('-',''))*1000000

  code=config['stocks'][0]
  df=pd.read_hdf('bundle/bundle/stocks.h5',key=code)
  df = df[ (df['datetime'] > start) & (df['datetime'] < end)]
  df['date'] = pd.to_datetime(pd.Series(df['datetime'], dtype="string"))
  df.index = df['date'] 
  df['date'] =df['date'].apply(lambda x:x.strftime('%Y-%m-%d'))
  print(df)

  trade_df = ret['sys_analyser']['trades']

  trade_df['date'] =pd.to_datetime(trade_df['datetime']).apply(lambda x:x.strftime('%Y-%m-%d'))

  print(trade_df)

  df['buy'] = np.nan
  df['sell'] = np.nan

  buytimes=trade_df[ trade_df[ 'side' ] == 'BUY' ]['date'].tolist()
  selltimes=trade_df[ trade_df[ 'side' ] == 'SELL' ]['date'].tolist()
  print('买入：', buytimes)
  print('卖出：', selltimes)

  indexs = df[df['date'].isin(buytimes)].index
  df.loc[indexs, 'buy'] = df.loc[indexs, 'open']

  indexs = df[df['date'].isin(selltimes)].index
  df.loc[indexs, 'sell'] = df.loc[indexs, 'close']

  my_color = mpf.make_marketcolors(up='red',#上涨时为红色
                                  down='green',#下跌时为绿色
                                  edge='i',#隐藏k线边缘
                                  volume='in',#成交量用同样的颜色
                                  inherit=True)

  my_style = mpf.make_mpf_style(gridaxis='both',#设置网格
                            gridstyle='-.',
                            y_on_right=True,
                              marketcolors=my_color)
  api = importlib.import_module(f'strategy.{strategy}')

  add_plot = [
      mpf.make_addplot(df['buy'], type='scatter', markersize=50, marker='^', color='purple'),
      mpf.make_addplot(df['sell'], type='scatter', markersize=50, marker='v', color='b'),
      
  ]
  api.append_indicator_draw(df, config, add_plot)
  mpf.plot(df,type='candle',
          style=my_style,
          addplot=add_plot,
          volume=True,
          figratio=(2,1),
          figscale=5,)
  
draw_indicator()