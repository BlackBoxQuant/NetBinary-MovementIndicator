from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters.morningstar import Q500US
import numpy as np
 
def initialize(context):
    #DEFAULT SLIPAGE
    context.R = 14
    context.newM = True
    context.Purged_Scores = []
    context.Purged_Shorts = []
    attach_pipeline(make_pipeline(), 'my_pipeline')
    context.Data_Dictionary = {}       
    schedule_function(sell, date_rules.month_start(), time_rules.market_close(minutes = 5))    
    schedule_function(buy, date_rules.month_start(), time_rules.market_close())
    schedule_function(new_month, date_rules.month_start(), time_rules.market_open())
def make_pipeline():
    Universe = Q500US()    
    pipe = Pipeline(screen = Universe)
    return pipe
def new_month (context, data):
    context.newM = True
def before_trading_start(context, data):
    L,S = 0,0
    for sec in context.portfolio.positions:
        if context.portfolio.positions[sec].amount > 0:
            L+=1
        if context.portfolio.positions[sec].amount < 0:
            S+=1
    record(Longs = L)
    record(Shorts = S)
    record(leverage = context.account.leverage)
    context.output = pipeline_output('my_pipeline')  
    context.List = context.output.index
    while context.newM == True:
        for sec in context.List:
            stockSymbol = str(sec.symbol)
            context.Data_Dictionary[stockSymbol] = 0.0
        for sec in context.List:
            stockSymbol = str(sec.symbol)
            Historical_Data = data.history(sec, "price", 390*10, "1m")
            for i in range(1,(390*10)):
                if i%1 == 0: # PLACEHOLDER - DOES NOTHING.
# NOT DEFAULT - GIVES SECURITIES THAT FALL OVER THE WHOLE TIME SERIES A BOOST, AND THOSE THAT RISE GET A PENALTY 
# Reasoning: Mean Reversion Theorem
# Results : Positive
                    old_price = (Historical_Data[i-60])#remember, 0 is the first value in the array, but, with HISTORICAL data, the first value is the "oldest"
                    new_price = (Historical_Data[i])
                    if new_price > old_price:
                        context.Data_Dictionary[stockSymbol] += 1
                    elif new_price < old_price: 
                        context.Data_Dictionary[stockSymbol] -= 1
        #we are done scoring stocks for this month: leave the while loop. 
        context.newM = False
                      
def sell (context, data):
    pass

def buy (context, data):
    scores = []
    Ordered_Scores = []
    Purged_Scores = []
    Purged_Shorts = []
    
    for score in context.Data_Dictionary.values():
        scores.append(score)
        
    Ordered_Scores = [int(X) for X in scores]
    Ordered_Scores.sort()
    Ordered_Scores.reverse()
    
    for i in range(0,context.R):
        Score = Ordered_Scores[i]
        Purged_Scores.append(Score)
        
    for i in range(-1*(context.R+1),-1):
        Score = Ordered_Scores[i]
        Purged_Shorts.append(Score)
        
    buyL = []
    buyS =[]
    k = str
    Order_Keys = []
    Order_Shorts = []
    Temp_Dictionary = {}
    
    for i in Purged_Scores:
        k = (list(context.Data_Dictionary.keys())[list(context.Data_Dictionary.values()).index(i)])
        Temp_Dictionary[str(k)] = context.Data_Dictionary[str(k)]
        del context.Data_Dictionary[k] 
        Order_Keys.append(k)
        
    for i in Purged_Scores:    
        k = (list(Temp_Dictionary.keys())[list(Temp_Dictionary.values()).index(i)])
        context.Data_Dictionary[str(k)] = Temp_Dictionary[str(k)]
        
    for sec in context.List:
        stockSymbol = str(sec.symbol)
        if stockSymbol in Order_Keys:
            buyL.append(sec)
       
    
    k = str
    Temp_Dictionary = {}
    
    for i in Purged_Shorts:
        k = (list(context.Data_Dictionary.keys())[list(context.Data_Dictionary.values()).index(i)])
        Temp_Dictionary[str(k)] = context.Data_Dictionary[str(k)]
        del context.Data_Dictionary[k] 
        Order_Shorts.append(k)
    for i in Purged_Shorts:    
        k = (list(Temp_Dictionary.keys())[list(Temp_Dictionary.values()).index(i)])
        context.Data_Dictionary[str(k)] = Temp_Dictionary[str(k)]
    for sec in context.List:
        stockSymbol = str(sec.symbol)
        if stockSymbol in (Order_Shorts):
            buyS.append(sec)

    if len(buyL) < 5:
        buyL = []
    if len(buyS) < 5:
        buyS = []
    for sec in context.portfolio.positions:
        if sec not in buyL or buyS:
            order_target_percent(sec, 0)
    for sec in buyL:
        order_target_percent(sec, 1.0/len(buyL))
    for sec in buyS:
        order_target_percent(sec, 0.0/len(buyS))
