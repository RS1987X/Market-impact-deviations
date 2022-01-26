# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 10:24:11 2022

@author: richa

Trade deviation from market impact model described by eq.1 in paper "The square-root impact law also holds for options markets
https://www.cfm.fr/assets/ResearchPapers/2016-The-square-root-impact-law-also-holds-for-option-markets.pdf

"""


import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import math
from datetime import date

#get prices from yahoo finance

tday = date.today()
tday_str = tday.strftime("%Y-%m-%d")


#tickers = ["EVO", "SINCH", "NIBE-B", "EQT", "MIPS", "STORY-B", "SF", "PDX", "SBB-B", "BALD-B", "SAGA-B"]
#tickers = ["ATCO-A"]
# =============================================================================
# tickers = ['BALD-B.ST', "SAGA-B.ST", 'SBB-B.ST', 'CAST.ST', 'WALL-B.ST', 'FABG.ST', 'CORE-B.ST', 'WIHL.ST', \
#            'NYF.ST', 'HUFV-A.ST', 'FPAR-A.ST', 'ATRLJ-B.ST', 'CATE.ST', 'NP3.ST', 'PLAZ-B.ST', \
#            'KFAST-B.ST', 'DIOS.ST', 'HEBA-B.ST', 'TRIAN-B.ST', 'CIBUS.ST', 'BONAV-B.ST', \
#            'PNDX-B.ST', 'JM.ST', 'SFAST.ST']
# =============================================================================

tickers = ["ABB","ALFA","ALIV-SDB","ASSA-B","ATCO-A","AZN","BOL","ELUX-B","ERIC-B","ESSITY-B","EVO","GETI-B","HEXA-B","HM-B","NDA-SE","SAND","SCA-B","SEB-A", \
           "SHB-A","SINCH","SKA-B","SKF-B","SWED-A","SWMA","TEL2-B","TELIA","VOLV-B"]
        

#tickers = [""]
long_short_returns = {}


for x in tickers:

    #=============================================================================
    # =============================================================================
    hist = yf.download(x + ".ST", start='2015-01-01', end=tday_str)
    # =============================================================================
    #=============================================================================
    # 
    # hist = yf.download('ALIG.ST CCC.ST BALCO.ST BERG-B.ST'
    #                    ' COIC.ST HLDX.S LIAB.ST MTRS.ST NCC-B.ST'
    #                    ' NMAN.ST SYSR.ST', start='2015-01-01', end=tday_str)
    
    close_prices = hist["Adj Close"]#.dropna(how='all').fillna(0)
    #volume traded each day
    Q = hist["Volume"].dropna(how='all').fillna(0).astype(float)
    #average daily volume traded each day
    V = Q.rolling(10).mean().shift(1)
    #calculate daily returns
    ret_daily = close_prices.pct_change()
    #calculate 5-day returns
    ret_5d = close_prices.pct_change(5)
    #calculate volatility
    sigma = ret_daily.rolling(10).std().shift(1)
    #numerical scaling constant
    Y = 0.7
    #calculate fair market impact of volume and realised market impact deviation
    market_impact_est = Y*sigma*np.sqrt(Q/V)
    
    sell_flow = ret_daily < 0
    buy_flow = ret_daily > 0
    signed_market_impact_est = -1*sell_flow*market_impact_est + buy_flow*market_impact_est 
    
    market_impact_deviation = ret_daily-signed_market_impact_est
    normal_deviation = market_impact_deviation.rolling(10).std().shift(1)
    
    long_ind = (market_impact_deviation > 0) & sell_flow &(Q>1*V)
    #short_ind = (market_impact_deviation < 0) & buy_flow & (Q>1*V)
    
    
    #calc transaction cost
    fee = 0.0002
    slippage = 0.05/100
    
    
    #fee = 0.06/100
    #replace false with NaN to avoid 0s impacting the mean
    #long_ind = long_ind.replace(False, np.nan)
    #short_ind = short_ind.replace(False, np.nan)
    long_returns_daily = ret_daily*long_ind.shift(1) - 2*fee*long_ind.shift(1) - 2*slippage*long_ind.shift(1)
    #short_returns_daily = -ret_daily*short_ind.shift(1) - 2*fee*short_ind.shift(1) - 2*slippage*long_ind.shift(1)

    #daily returns of long short strategy
    #avg_long_ret = starting_capital*long_returns_daily.mean(axis=1)-transaction_cost
    #avg_long_ret = long_returns_daily.mean()-trans_proc_fee-slippage
    #avg_short_ret = short_returns_daily.mean(axis=1)-trans_proc_fee
    
    
    #avg_daily_rets  = daily_returns_strat.mean(axis=1)
    
    #combined_long_short = pd.concat([long_strat_returns, short_strat_returns],axis=0)
    #combined_long_short = combined_long_short.sort_index()
    #combined_long_short = combined_long_short.to_frame()
    long_short_returns.update(long_returns_daily)#+short_returns_daily)

returns = pd.DataFrame(list(long_short_returns.items()),columns=["index", "returns"])
returns = returns.set_index("index")
returns = returns.sort_index()

cum_ret_w_zeroes = (1 + returns["returns"]).cumprod()

returns_wo_zeroes = returns.replace(False,np.nan)
#Cumulative returns 
#cum_ret =starting_capital +  np.cumsum(daily_returns_strat) #
cum_ret =(1 + returns_wo_zeroes["returns"]).cumprod()

#cum_long_ret =  (1 + avg_long_ret).cumprod()
#cum_short_ret =  (1 + avg_short_ret).cumprod()


###########################################
#stats for basic strategy
##########################################

print("   ")
print('Market impact deviation ')
CAGR = cum_ret[cum_ret.last_valid_index()]**(1/7)-1
print("CAGR " + str(CAGR))
mean_ret = returns_wo_zeroes.mean()
vol = (returns_wo_zeroes.std())
ann_vol = returns_wo_zeroes.std()*math.sqrt(long_ind.sum()/7)
sharpe = CAGR/ann_vol
kelly_f = mean_ret/vol**2
print("Return per trade " + str(returns_wo_zeroes.mean()))
print("Volatility " + str(ann_vol))
print("Sharpe " + str(sharpe))
print("Kelly fraction " + str(kelly_f))
#maxiumum drawdown
Roll_Max = cum_ret.cummax()
Daily_Drawdown = cum_ret/Roll_Max - 1.0
Max_Daily_Drawdown = Daily_Drawdown.cummin()
print("Max drawdown " + str(Max_Daily_Drawdown.tail(1)[0]))

#plots
plt.plot(cum_ret_w_zeroes)
# =============================================================================
# 
# ###################################################
# #modified strategy considering factor momentum
# ####################################################
# 
# mom_cum_ret = (1+daily_returns_strat[cum_ret.pct_change(20).shift(1) > 0]).cumprod() #
# #mom_cum_ret = starting_capital + np.cumsum(daily_returns_strat[cum_ret.pct_change(20).shift(1) > 0])
# mom_daily_ret_IND = mom_cum_ret.pct_change()
# 
# 
# mom_mean_ret = mom_cum_ret.tail(1)**(1/7)-1
# 
# mom_vol = (daily_returns_strat[cum_ret.pct_change(20).shift(1) > 0].std()*math.sqrt(252)) #
# mom_sharpe = mom_mean_ret/mom_vol
# mom_kelly_f = mom_mean_ret/mom_vol**2
# 
# #maxiumum drawdown
# mom_Roll_Max = mom_cum_ret.cummax()
# mom_Daily_Drawdown = mom_cum_ret/mom_Roll_Max - 1.0
# mom_Max_Daily_Drawdown = mom_Daily_Drawdown.cummin()
# print("   ")
# print('Short term reversal with factor momentum INDUSTRIALS')
# print("CAGR " + str(mom_mean_ret[0]))
# print("Volatility " + str(mom_vol))
# 
# print("Sharpe " + str(mom_sharpe[0]))
# print("Kelly fraction " + str(mom_kelly_f[0]))
# #maxiumum drawdown
# Roll_Max = cum_ret.cummax()
# Daily_Drawdown = cum_ret/Roll_Max - 1.0
# Max_Daily_Drawdown = Daily_Drawdown.cummin()
# print("Max drawdown " + str(mom_Max_Daily_Drawdown.tail(1)[0]))
# 
# #calculate log returns st reversal momentum strategy and print returns per year
# mom_log_ret_IND = np.log(mom_cum_ret)-np.log(mom_cum_ret.shift(1))
# per = mom_log_ret_IND.index.to_period("Y")
# g = mom_log_ret_IND.groupby(per)
# ret_per_year = g.sum()
# print("   ")
# print("st reversal INDUSTRIALS with factor momentum returns per year")
# print(ret_per_year)
# 
# 
# per_M = mom_log_ret_IND.index.to_period("M")
# grouping_month = mom_log_ret_IND.groupby(per_M)
# ret_per_month = grouping_month.sum()
# #stats for monthly returns
# percent_positive = ret_per_month[ret_per_month>0].count()/ret_per_month.count()
# print("")
# print("percent positive months " + str(percent_positive))
# 
# 
# plt.plot(mom_cum_ret)
# 
# 
# ################
# #buy and hold
# ################
# avg_ret_boh= ret_daily.mean(axis=1)
# cum_ret_boh =  (1 + avg_ret_boh).cumprod()
# #avg_ret_boh= starting_capital*ret_daily.mean(axis=1)
# #cum_ret_boh =  starting_capital + np.cumsum(avg_ret_boh)
# plt.plot(cum_ret_boh)
# 
# 
# #stats buy and hold
# print("   ")
# print('Buy and hold stats')
# boh_mean_ret = cum_ret_boh.tail(1)**(1/7)-1
# boh_vol = (avg_ret_boh.std()*math.sqrt(252))
# boh_sharpe = boh_mean_ret/boh_vol
# boh_kelly_f = boh_mean_ret/boh_vol**2
# 
# #maxiumum drawdown
# boh_Roll_Max = cum_ret_boh.cummax()
# boh_Daily_Drawdown = cum_ret_boh/boh_Roll_Max - 1.0
# boh_Max_Daily_Drawdown = boh_Daily_Drawdown.cummin()
# 
# 
# 
# print("CAGR " + str(boh_mean_ret[0]))
# print("Volatility " + str(boh_vol))
# 
# print("Sharpe " + str(boh_sharpe[0]))
# print("Kelly fraction " + str(boh_kelly_f[0]))
# 
# print("Max drawdown " + str(boh_Max_Daily_Drawdown.tail(1)[0]))
# 
# print(" ")
# 
# print('40-day momentum of short term reversal INDUSTRIALS strategy')
# print(cum_ret.pct_change(40).tail(1))
# =============================================================================
