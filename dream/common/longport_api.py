#!/bin/python3

# System lib
import os
import sys

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from longport.openapi import Config, TradeContext, QuoteContext
from longport.openapi import Period, AdjustType
from longport.openapi import OrderSide, OrderType, TimeInForceType
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_secret as dbds

def quantitative_init(quant_type, user):
    db = dbds.db('dream_sentiment')
    if (not db.is_table_exist()):
        #log.get().info('Quantitative table not exist, new a table...')
        db.create_secret_table()
    res = db.query_secret_by_type(quant_type, user)
    if len(res) != 1:
        return
    os.environ['LONGPORT_APP_KEY'] = res[0].App_Key
    os.environ['LONGPORT_APP_SECRET'] = res[0].App_Secret
    os.environ['LONGPORT_ACCESS_TOKEN'] = res[0].Access_Token

def get_trade_context():
    trade_ctx = TradeContext(Config.from_env())
    return trade_ctx

def get_quote_context():
    quote_ctx = QuoteContext(Config.from_env())
    return quote_ctx

def get_history(id, **kwargs):
    ctx = get_quote_context()
    resp = ctx.history_candlesticks_by_date(id, Period.Day,
        AdjustType.ForwardAdjust, **kwargs)
    return resp

# LO (Limit Order): (目前都以这个为默认先，学习其他量化知识再升级交易接口)
# 限价单，在设定的价格或更好的价格执行交易。买单会在设定价格或更低价格执行，卖单会在设定价格或更高价格执行。
# MIT (Market If Touched):
# 触价市价单，当市场价格触及某个预设水平时，触发并转为市价单，按市场当前价格成交。
# MO (Market Order):
# 市价单，按市场当前价格立即执行的订单，不保证价格，但保证成交
def trade_submit(dog_id, side, price, share):
    if side == 'sell':
        order_side = OrderSide.Sell
    elif side == 'buy':
        order_side = OrderSide.Buy
    else:
        return None
    ctx = get_trade_context()
    resp = ctx.submit_order(symbol = dog_id,
        side = order_side, order_type = OrderType.LO, 
        submitted_price = round(price, 2),
        submitted_quantity = int(share),
        time_in_force = TimeInForceType.Day,
        remark = "%s"%(side),
    )
    return resp