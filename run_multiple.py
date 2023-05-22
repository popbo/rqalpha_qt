from concurrent.futures import ProcessPoolExecutor
from rqalpha import run_file
import yaml
from itertools import *
import multiprocessing
from copy import deepcopy
import traceback
import os
import sqlite3
import sys

sys.setrecursionlimit(1000000)

__g_config__ = {
  "base": {
    "data_bundle_path": "bundle/bundle",
    "start_date": "2017-03-05",
    "end_date": "2018-03-07",
    "benchmark": "000001.XSHE",
    "frequency": "1d",
    "accounts": {
        "stock": 100000
    }
  },
  "extra": {
    "log_level": "error",
  },
  "mod": {
    "sys_analyser": {
      "enabled": True,
      #"plot": True,
    }
  },
  "stocks": ["000001.XSHE"]
}

__strategy_file_path__ = "./strategy/"
__config_file_path__ = "./config/multiple/"
__strategy_results_path__ = "./results/"

def read_config_file(config_file):
    f = open(config_file, 'r', encoding='utf-8')
    return yaml.safe_load(f.read())

def get_all_config(dict_conf):
    keys = list(dict_conf.keys())
    paras = [list(range(v['min'], v['max']+1, v['step'])) for v in dict_conf.values()]
    confs = list(product(*paras))

    return [{keys[i]: cf[i] for i in range(len(keys))} for cf in confs]

def create_db(dbfile, dict_config):
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()

    createtb_sql = 'create table result('
    for key in dict_config:
        createtb_sql=createtb_sql+key+' '+dict_config[key]['type']+', '
    createtb_sql = f'{createtb_sql}total_returns float,excess_returns float,max_drawdown float,sharpe float);'
    cur.execute(createtb_sql)

    cur.close()
    conn.close()

def insert_db(dbfile, result):
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()

    summary=result['result']['sys_analyser']['summary']
    conf=",".join(map(str, list(result['config'].values())))
    insert_sql=f"insert into result values ({conf},{round(summary['total_returns'],4)},{round(summary['excess_returns'],4)},{round(summary['max_drawdown'],4)},{round(summary['sharpe'],4)})"
    cursor.execute(insert_sql)

    cursor.close()
    conn.commit()
    conn.close()
    

def single_strategy(task):
    strategy_file, db_file, conf = task
    ret=None
    try:
        print(os.getpid(), conf['paras'])
        ret = run_file(strategy_file, conf)
    except Exception as e:
        traceback.print_exc()
    result = {'config': conf['paras'], 'result': ret}
    insert_db(db_file, result)


def multiple_strategy(strategy_name):
    strategy_file = __strategy_file_path__+strategy_name+'.py'
    config_file = __config_file_path__+strategy_name+'.yml'
    db_file = __strategy_results_path__ + strategy_name + '.db'

    dict_config = read_config_file(config_file)
    create_db(db_file, dict_config)

    myconfigs=get_all_config(dict_config)
    tasks=[]
    for myconf in myconfigs:
        config = deepcopy(__g_config__)
        config['paras']=myconf
        tasks.append((strategy_file, db_file, config))

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for task in tasks:
            executor.submit(single_strategy, task)

    print('success')


if __name__ == "__main__":
    #single_strategy()
    multiple_strategy('kdj')