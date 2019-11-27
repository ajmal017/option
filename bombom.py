# http://www.liujiangblog.com/course/python/82
# 20190902 future work
# analysis_statement當做基本面filter
# 將通過analysis_statement當做基本面filter的股票下載yahoo finance的.csv
# 再算get_supporting_point

# https://github.com/dsmbgu8/image_annotate.py/issues/4
# echo "backend: TkAgg" >> ~/.matplotlib/matplotlibrc

# 20190925
#ok 1.
#ok stress要取區間value*volume
# 2.
# 加上Stress,close%	stress/hold（put顯示stress > strike、call顯示stress < strike）
# put看支撐, call看壓力
# put 是不希望跌到你的strike，所以要找一個option 有一個hold 高於strike，表示當股價跌到hold 有撐，不容易讓你履約
# 3.
# 總表
#ok 4.
#ok MA40、MA80 state

# 20191027
# 1. 要卡+ or - 的distance

# 20191116
# 1. 找contract的履約價跟我們close的價差delta_d，去歷史看在到履約日期內的時間長度delta_p，有幾次會下跌or上漲delta_p
#    ->幾天後，下跌or上漲delta_p的機率
# 2. 再考慮各種技術指標的組合情況

# 20191117
# 1. some bug in do_back_testing()

import sys
#sys.path.insert(0, '/home/ckwang/.local/lib/python2.7/site-packages')
#sys.path.insert(0, '/usr/local/lib/python3.5/dist-packages')
import copy
import argparse
import multiprocessing
from multiprocessing import Process
from multiprocessing import queues
import time
import pickle
import os

from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
#import fix_yahoo_finance as yf

import finviz
import copy
import requests
import pandas as pd

import yfinance as yf
import csv

from finviz.screener import Screener

import json

# dary
import operator

import datetime
from datetime import timedelta
from datetime import date as dt

import glob

#print (finviz.get_stock('AMD'))
#assert False
# Optionable
# Avg Volume
# EPS (ttm)
# EPS next Y
# EPS next Q
# EPS this Y
# EPS next 5Y
# EPS past 5Y
# EPS Q/Q
# 

#assert False

# self.ma_days = 200
# stock_dict = {	supported_point: [{  Interval: xxx 
#										vol_val: xxx	}, {...}, {...}],

#					topk_vol:		[0, 0, top1_volume, 0, 0, 0, top2_volume.....],

#					moving_average: {'2012-02-14': {'type': big_cow,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									'2012-02-1X': {'type': small_bear,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									....}
#				}

class Trader(object):
	def __init__(self, period_days, difference_rate, stock_folder_path, option_folder_path, roe_ttm):
		self.stock_name = -1
		self.period_days = period_days
		self.difference_rate = 0.1#difference_rate
		self.roe_ttm = roe_ttm
		self.stock_folder_path = stock_folder_path
		self.option_folder_path = option_folder_path
		self.techidx_folder_path = 'techidx'
		
		self.option_com_order_folder_path = 'final_'+time.strftime("%Y-%m-%d", time.localtime())
		self.value_group = -1
		self.top_volume_num = 10
		self.part_num = 100
		self.ma_days = 200
		self.nKD = 9
		self.bid_strike_thre = 0.03 #(bid-ask)/strike
		self.PCS_clos_suppo_dist = 0.1
		self.CCS_clos_press_dist = 0.1
		self.supported_point_rate_thre = 0.5
		self.pressed_point_rate_thre = 0.5
		self.PCS_return_on_invest = 0.03
		self.CCS_return_on_invest = 0.03
		self.min_days = 300 * 6
		self.interval_value_point = 3
		self.combine_contract_delta_value = 10
		self.combine_contract_ratio = 0.8
		self.sp_close_ratio = 0.7
		self.sc_close_ratio = 1.3
		self.analysis_statement_status = 1  #0: don't care, 1: basic(volume & optionable), 2: all function in analysis_statement()
		self.un_hit_probability_thre = 0.1

	def best_contract(self, stock_name):
		period_days = 5
		difference_rate = 0.1
		stock_folder_path = 'stocks'
		options_folder_path = 'options'
		roe_ttm = 1
		t = Trader(period_days, difference_rate, stock_folder_path, options_folder_path, roe_ttm)

		#stock_name = 'ZION'# ZION AMD
		file_path = 'stocks/{}.csv'.format(stock_name)
		tech_idx_path = 'techidx/{}.csv'.format(stock_name)

		#import time
		#start = time.time()
		m = 20*250
		valid_percentage_sup_pnt_threthod = 0.5
		sup_pnt_close_interval = 100
		valid_percentage_press_pnt_threthod = 0.5
		press_pnt_close_interval = 100

		MACD_short=12
		MACD_long=26
		MACD_signallength=9
		
		stock_tech_idx_dict = {}
		stock_tech_idx_dict = t.get_stock_value(file_path, stock_tech_idx_dict, m=m)
		stock_tech_idx_dict = t.get_KD(file_path, stock_tech_idx_dict, nBin=5, nKD=9, m=m)
		stock_tech_idx_dict = t.get_RSI(file_path, stock_tech_idx_dict, nBin=5, n=6, m=m)
		stock_tech_idx_dict = t.get_MA(file_path, stock_tech_idx_dict, Total_day=m-200, percent=1)

		stock_tech_idx_dict = t.get_MACD(file_path, stock_tech_idx_dict, Total_day_MACD=m, MACD_short=MACD_short, MACD_long=MACD_long, MACD_signallength=MACD_signallength)

		stock_tech_idx_dict = t.get_supported_point(file_path, stock_tech_idx_dict, sup_pnt_close_interval=sup_pnt_close_interval, valid_percentage_sup_pnt_threthod=valid_percentage_sup_pnt_threthod)
		stock_tech_idx_dict = t.get_pressed_point(file_path, stock_tech_idx_dict, press_pnt_close_interval=press_pnt_close_interval, valid_percentage_press_pnt_threthod=valid_percentage_press_pnt_threthod)

		t.output_tech_idx(tech_idx_path, stock_tech_idx_dict)
		del t

	def back_testing_byDTree(self, tech_idx_path, tech_idx_dict_today):
		close = tech_idx_dict_today['Close']
		MA = tech_idx_dict_today['MA']
		MACD = tech_idx_dict_today['MACD']
		D = tech_idx_dict_today['D']
		RSI = tech_idx_dict_today['RSI']
		Pressed_point = tech_idx_dict_today['Pressed_point']
		Supported_point = tech_idx_dict_today['Supported_point']
		strike_date = tech_idx_dict_today['strike_date']
		strike_price = tech_idx_dict_today['strike_price']

		training_data_list_all = []
		ground_list_all = []


		delta_d = self.get_date_diff(strike_date, dt.today().strftime("%Y-%m-%d"))
		#delta_p = strike_price / close # strike_price / close
		df = pd.read_csv(tech_idx_path)
		df_shape = df.shape
		reuslt_dict = {'all': 0, 'unhit': 0}
		for num_of_date in range(1, df_shape[0]-delta_d):
			training_data_list = []
			row = df[:][num_of_date:num_of_date+1] # Close,MA,MACD,D,RSI,Supported_point,Pressed_point
			row_future = df[:][num_of_date+delta_d:num_of_date+delta_d+1]
			training_data_list = [float(row['MA'].values), float(row['MACD'].values), float(row['D'].values), float(row['RSI'].values), ]
			if typ == 'put':
				# 歷史資料future - now > 該合約
				# 歷史資料中第n+30天的close(27) - 歷史資料中第n天的close(28) > strike_price(25) - now_close(28)
				if row_future['Close'].values / row['Close'].values > strike_price / close:
					reuslt_dict['unhit']+=1
#				if row['Close'].values - row_future['Close'].values < close - strike_price:
#					reuslt_dict['unhit']+=1
			elif typ == 'call':
				# 歷史資料future - now < 該合約
				if row_future['Close'].values / row['Close'].values < strike_price / close:
					reuslt_dict['unhit']+=1
			else:
				assert False, 'wrong with contract type in do_back_testing'
		if reuslt_dict['all'] == 0:
			return 0.0
		return reuslt_dict

	# supported_point: 確認strike跟close中間有supported_point
	@staticmethod
	def check_vaild_sample(do_tech_idx_dict, today_tech_idx, strike_price):
		for tech_idx in do_tech_idx_dict.keys():
			if 'Supported_point' in tech_idx:
				'''
				close_value = today_tech_idx['Close'].values
				Supported_point_dict = json.loads(u'{}'.format(do_tech_idx_dict[tech_idx][0]))
				with_sup_pnt_flag = False
				for sup_pnt_value in Supported_point_dict.keys():
					if close_value > float(sup_pnt_value) and float(sup_pnt_value) > strike_price:
						with_sup_pnt_flag = True
				if not with_sup_pnt_flag:
					return False
					'''
				close_value = today_tech_idx['Close'].values
				pcs_ratio = strike_price / close_value
				Supported_point_dict = json.loads(u'{}'.format(do_tech_idx_dict[tech_idx][0]))
				with_sup_pnt_flag = False
				for sup_pnt_value in Supported_point_dict.keys():
					if close_value > float(sup_pnt_value) and float(sup_pnt_value) > close_value*pcs_ratio:
						with_sup_pnt_flag = True
				if not with_sup_pnt_flag:
					return False

			elif 'Pressed_point' in tech_idx:
				'''
				close_value = today_tech_idx['Close'].values
				Pressed_point_dict = json.loads(u'{}'.format(do_tech_idx_dict[tech_idx][0]))
				with_press_pnt_flag = False
				for press_pnt_value in Pressed_point_dict.keys():
					if close_value < float(press_pnt_value) and float(press_pnt_value) < strike_price:
						with_press_pnt_flag = True
				if not with_press_pnt_flag:
					return False
					'''
				close_value = today_tech_idx['Close'].values
				ccs_ratio = strike_price / close_value
				Pressed_point_dict = json.loads(u'{}'.format(do_tech_idx_dict[tech_idx][0]))
				with_press_pnt_flag = False
				for press_pnt_value in Pressed_point_dict.keys():
					if close_value < float(press_pnt_value) and float(press_pnt_value) < close_value*ccs_ratio:
						with_press_pnt_flag = True
				if not with_press_pnt_flag:
					return False

			else: # Close,MA,MACD,D,RSI,Supported_point,Pressed_point
				try:
					#print (tech_idx, int(do_tech_idx_dict[tech_idx]), int(today_tech_idx[tech_idx].values))
					if not (int(do_tech_idx_dict[tech_idx]) == int(today_tech_idx[tech_idx].values)):
						return False
				except:
					print ('2-1: ', do_tech_idx_dict)
					print ('2-2: ', today_tech_idx)
					print ('2-3: ', int(do_tech_idx_dict[tech_idx]))
					print ('2-4: ', today_tech_idx[tech_idx])
					print ('2-5: ', int(today_tech_idx[tech_idx].values))
					assert False
		return True

	@staticmethod
	def get_date_diff(date1, date2):
		datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
		date1 = '{} 10:01:28.585'.format(date1)
		date2 = '{} 09:56:28.067'.format(date2)
		diff = datetime.datetime.strptime(date1, datetimeFormat) - datetime.datetime.strptime(date2, datetimeFormat)
		return diff.days

	def do_back_testing(self, tech_idx_path, close, sell_strike_price, buy_strike_price, strike_date, do_tech_idx_dict, typ):
		# Input:
		#		tech_idx_path: the path of tech index csv file
		#		delta_d: the time length of tody ~ strike date -> 幾天後
		#		delta_p: the different of price between close of today and strike price 
		#			-> strike_price - today_close
		#		do_tech_idx_dict: {'MA': 1, 'RSI': 3, 'Supported_point': {'31': 1, '37': 0.85...}}
		#		typ: SP or BP
		# Output:
		#		在detla_d的時間間隔內，且起始日期符合do_tech_idx_dict的條件的樣本，不會產生detla_p的價格幅度
		# 1. 確認是有效樣本（技術指標符合）
		# 2. 確認delta_d天後的漲跌幅是否<delta_p
		# 3. update

		delta_d = self.get_date_diff(strike_date, dt.today().strftime("%Y-%m-%d"))
		#print ('strike_date: {}	do_tech_idx_dict: {}'.format(strike_date, do_tech_idx_dict.keys()))
		#if delta_d > 60:
		#	return
		#delta_p = strike_price - close # future - now
		df = pd.read_csv(tech_idx_path)
		df_shape = df.shape
#		reuslt_dict = {'all': 0, 'unhit': 0}
		reuslt_dict = {'all': 0, 'p1': 0, 'p2': 0, 'p3': 0}
		if delta_d < 0:
			return reuslt_dict
		for num_of_date in range(1, df_shape[0]-delta_d):
			#print ('num_of_date: ', num_of_date, ' df_shape[0]: ', df_shape[0], ' delta_d: ', delta_d)
			row = df[:][num_of_date:num_of_date+1] # Close,MA,MACD,D,RSI,Supported_point,Pressed_point
			#print ('row: ', row, ' num_of_date: ', num_of_date, ' df_shape: ', df_shape, ' delta_d: ', delta_d)
			if not self.check_vaild_sample(do_tech_idx_dict, row, sell_strike_price):
				continue
			reuslt_dict['all']+=1
			row_future = df[:][num_of_date+delta_d:num_of_date+delta_d+1]
			if typ == 'put':
#				if row_future['Close'].values / row['Close'].values > strike_price / close:
#					reuslt_dict['unhit']+=1
				if row_future['Close'].values / row['Close'].values > sell_strike_price / close:
					reuslt_dict['p1']+=1
				elif sell_strike_price / close >= row_future['Close'].values / row['Close'].values >= buy_strike_price / close:
					reuslt_dict['p2']+=1
				elif row_future['Close'].values / row['Close'].values < buy_strike_price / close:
					reuslt_dict['p3']+=1
				else:
					assert False, 'wrong with do_back_testing range, in {}'.format(typ)

			elif typ == 'call':
				# 歷史資料future - now < 該合約
#				if row_future['Close'].values / row['Close'].values < strike_price / close:
#					reuslt_dict['unhit']+=1
				if row_future['Close'].values / row['Close'].values < sell_strike_price / close:
					reuslt_dict['p1']+=1
				elif sell_strike_price / close <= row_future['Close'].values / row['Close'].values <= buy_strike_price / close:
					reuslt_dict['p2']+=1
				elif row_future['Close'].values / row['Close'].values > buy_strike_price / close:
					reuslt_dict['p3']+=1
				else:
					assert False, 'wrong with do_back_testing range, in {}'.format(typ)
			else:
				assert False, 'wrong with contract type in do_back_testing'
		#if reuslt_dict['all'] == 0:
		#	return 0.0
		return reuslt_dict

	@staticmethod
	def get_back_testing_bechmark_keyvalues(keys_all, row_lasted):
		bechmark_dict = {}
		keys_list = keys_all.split('-')
		#print (row_lasted, keys_list, keys_all)
		for key in keys_list:
			bechmark_dict[key] = row_lasted[key].values
		return bechmark_dict, keys_all

	@staticmethod
	def check_sup_press_point(row_lasted, close_value, sell_strike, contract_typ):
		typ = 'Supported_point' if contract_typ == 'put' else 'Pressed_point'
		if typ == 'Pressed_point':
			Pressed_point_dict = json.loads(u'{}'.format(row_lasted[typ].values[0]))
			with_press_pnt_flag = False
			for press_pnt_value in Pressed_point_dict.keys():
				if close_value < float(press_pnt_value) and float(press_pnt_value) < sell_strike:
					with_press_pnt_flag = True
			if not with_press_pnt_flag:
				return False
		elif typ == 'Supported_point':
			Supported_point_dict = json.loads(u'{}'.format(row_lasted[typ].values[0]))
			with_sup_pnt_flag = False
			for sup_pnt_value in Supported_point_dict.keys():
				if close_value < float(sup_pnt_value) and float(sup_pnt_value) < sell_strike:
					with_sup_pnt_flag = True
			if not with_sup_pnt_flag:
				return False
		else:
			assert False, 'typ wrong with {}'.format(typ)

	def back_testing(self, tech_idx_path, options_contract_file_path, combin_contract_list_all):
		# 1. 找contract的履約價跟我們close的價差delta_p，去歷史看在到履約日期內的時間長度delta_d，
		#		有幾次會下跌or上漲delta_p的機率
		# 2. 再考慮各種技術指標的組合情況
		# MA MACD D RSI
		# 1 1 1 1
		# 1 1 1 0
		# 1 1 0 1
		# 1 1 0 0
		# 1 0 1 1
		# 1 0 1 0
		# 1 0 0 1
		# 1 0 0 0



		keys_list = ['MACD-D']#['MA-MACD-D-RSI', 'MA-MACD-D', 'MA-MACD-RSI', 'MA-MACD', \
					#'MA-D-RSI', 'MA-D', 'MA-RSI', 'MA', \
					#'MACD-D-RSI', 'MACD-D', 'MACD-RSI', 'MACD', \
					#'D-RSI', 'D', 'RSI', '']

		#print (tech_idx_path)
		df_tech_idx = pd.read_csv(tech_idx_path)
		close_value = -1
		row_lasted = -1

		for num in range(1, df_tech_idx.shape[0]):
			row_lasted = df_tech_idx[:][num:num+1]
		#	close_value = row_lasted['Close'].values
		#print (combin_contract_list_all)
		#df_contracts = pd.read_csv(options_contract_file_path)
		#for num_contracts in range(1, df_contracts.shape[0]):
		#	row_contracts = df_contracts[:][num_contracts:num_contracts+1]
		#	typ = row_contracts['type'].values
		#	strike_price = row_contracts['strike'].values
		#	strike_date = row_contracts['date'].values
		#	print ('strike_price: {} 	strike_date: {}'.format(strike_price, strike_date))
		win_probability_dict_buy = {}
		win_probability_dict_sell = {}
		# 技術指標全部都看，期望值最高的
		# 技術指標全部都看，然後勝率最高的
		best_combin_contract_all = {}
		best_combin_contract_all_list = []
		for combin_contract_list in combin_contract_list_all:
			#print (combin_contract_list)
			best_combin_contract = {'sell_contractSymbol': -1, \
									'buy_contractSymbol': -1, \
									'except_value': 0, \
									'sample_num': -1}
			for combin_contract in combin_contract_list:
				
				close_value = combin_contract['lasted_close']
				typ = combin_contract['contract_type'][0]
				# sell part
				sell_strike_price = combin_contract['sell_strike_price']
				buy_strike_price = combin_contract['buy_strike_price']
				strike_date = combin_contract['sell_strike_date']
				probability_reuslt_dict_all = {}
				if not self.check_sup_press_point(row_lasted, close_value, sell_strike_price, typ):
					continue
				for keys in keys_list:
					if typ == 'put':
						keys_all = '{}-{}'.format(keys, 'Supported_point') if keys != '' else 'Supported_point'
					elif typ == 'call':
						keys_all = '{}-{}'.format(keys, 'Pressed_point') if keys != '' else 'Pressed_point'
					else:
						assert False, 'wrong with contract type: {}'.format(typ)
					do_tech_idx_dict, keys_all = self.get_back_testing_bechmark_keyvalues(keys_all, row_lasted)
					probability_reuslt_dict = self.do_back_testing(tech_idx_path, close_value, sell_strike_price, buy_strike_price, strike_date, do_tech_idx_dict, typ)
					probability_reuslt_dict_all[keys_all] = copy.deepcopy(probability_reuslt_dict)

				for keys_all in keys_list[:-1]:
					do_tech_idx_dict, keys_all = self.get_back_testing_bechmark_keyvalues(keys_all, row_lasted)
					probability_reuslt_dict = self.do_back_testing(tech_idx_path, close_value, sell_strike_price, buy_strike_price, strike_date, do_tech_idx_dict, typ)
					probability_reuslt_dict_all[keys_all] = copy.deepcopy(probability_reuslt_dict)
				#print (win_probability_dict_sell)

				## buy part
				#strike_price = combin_contract['buy_strike_price']
				#strike_date = combin_contract['buy_strike_date']
				#for keys in keys_list:
				#	if typ == 'put':
				#		keys_all = '{}-{}'.format(keys, 'Supported_point') if keys != '' else 'Supported_point'
				#	elif typ == 'call':
				#		keys_all = '{}-{}'.format(keys, 'Pressed_point') if keys != '' else 'Pressed_point'
				#	else:
				#		assert False, 'wrong with contract type: {}'.format(typ)
				#	do_tech_idx_dict, keys_all = self.get_back_testing_bechmark_keyvalues(keys_all, row_lasted)
				#	probability_reuslt_dict = self.do_back_testing(tech_idx_path, close_value, strike_price, strike_date, do_tech_idx_dict, typ)
				#	win_probability_dict_buy[keys_all] = copy.deepcopy((probability_reuslt_dict['all'] - probability_reuslt_dict['unhit']) / probability_reuslt_dict['all'])
				#
				#for keys_all in keys_list[:-1]:
				#	do_tech_idx_dict, keys_all = self.get_back_testing_bechmark_keyvalues(keys_all, row_lasted)
				#	probability_reuslt_dict = self.do_back_testing(tech_idx_path, close_value, strike_price, strike_date, do_tech_idx_dict, typ)
				#	win_probability_dict_buy[keys_all] = copy.deepcopy((probability_reuslt_dict['all'] - probability_reuslt_dict['unhit']) / probability_reuslt_dict['all'])
				
				if typ == 'call':
					prob_dict = probability_reuslt_dict_all['MACD-D-Pressed_point']
					except_value = (prob_dict['p1']/(prob_dict['all']+0.001)) * (combin_contract['bid']-combin_contract['ask']) \
								+ (prob_dict['p2']/(prob_dict['all']+0.001)) * (sell_strike_price-buy_strike_price+combin_contract['bid']-combin_contract['ask']) \
								+ (prob_dict['p3']/(prob_dict['all']+0.001)) * (sell_strike_price-buy_strike_price+combin_contract['bid']-combin_contract['ask'])
				elif typ == 'put':
					prob_dict = probability_reuslt_dict_all['MACD-D-Supported_point']
					except_value = (prob_dict['p1']/(prob_dict['all']+0.001)) * (combin_contract['bid']-combin_contract['ask']) \
								+ (prob_dict['p2']/(prob_dict['all']+0.001)) * (buy_strike_price-sell_strike_price+combin_contract['bid']-combin_contract['ask']) \
								+ (prob_dict['p3']/(prob_dict['all']+0.001)) * (buy_strike_price-sell_strike_price+combin_contract['bid']-combin_contract['ask'])

				else:
					assert False, 'wrong with except_value tpye: {}'.format(typ)
				#if except_value > 0:
				#	print ('except_value: ', except_value, combin_contract['sell_contractSymbol'])#, combin_contract['buy_contractSymbol'])

				#if best_combin_contract['except_value'] < except_value:
				if True:
					best_combin_contract['close'] = combin_contract['lasted_close']
					best_combin_contract['sell_contractSymbol'] = combin_contract['sell_contractSymbol']
					best_combin_contract['buy_contractSymbol'] = combin_contract['buy_contractSymbol']
					best_combin_contract['except_value'] = except_value
					best_combin_contract['sample_num'] = probability_reuslt_dict['all']
					best_combin_contract['un_hit_probability'] = probability_reuslt_dict['p1'] / (probability_reuslt_dict['all']+0.001)
					best_combin_contract['return_on_invest'] = combin_contract['return_on_invest']
					best_combin_contract['date'] = strike_date
					if best_combin_contract['un_hit_probability'] > self.un_hit_probability_thre:
						#best_combin_contract_all[strike_date] = copy.deepcopy(best_combin_contract)
						best_combin_contract_all_list.append(copy.deepcopy(best_combin_contract))
		return best_combin_contract_all_list
		#return best_combin_contract_all


	def get_best_combination_contract(self, sell_contracts_list, buy_contracts_list, contract_type):
		#print (sell_contracts_list)
		PCS_combin_contract_list = []
		CCS_combin_contract_list = []
		#print (sell_contracts_list, buy_contracts_list)
		# PCS=SP+BP, the strike of SP need to > BP
		#### hard code parameter, don't care this parameter right now ###
		combine_contract_delta_value = self.combine_contract_delta_value
		if contract_type == 'put':
			for sell_contracts_dict in sell_contracts_list:
				for buy_contracts_dict in buy_contracts_list:
					combin_contract_dict = {'sell_contractSymbol': -1, \
											'buy_contractSymbol': -1, \
											'return_on_invest': -1, \
											'risk_max': -1, \
											'string': -1, \
											'sell_strike_date': -1, \
											'buy_strike_date': -1, \
											'sell_strike_price': -1, \
											'buy_strike_price': -1, \
											'contract_type': contract_type, \
											'lasted_close': sell_contracts_dict['lasted_close']}
					sell_bid = float(sell_contracts_dict['bid'])
					buy_ask = float(buy_contracts_dict['ask'])
					#print (sell_bid, sell_contracts_dict['strike'], buy_ask, buy_contracts_dict['strike'])
					#print (sell_contracts_dict['strike'] < buy_contracts_dict['strike'], sell_contracts_dict['strike'], buy_contracts_dict['strike'])
					if sell_contracts_dict['strike'] <= buy_contracts_dict['strike']:
						continue
					if sell_bid <= buy_ask:
						continue
					if sell_contracts_dict['lasted_close']*self.sp_close_ratio > sell_contracts_dict['strike']:
						continue
					#print (sell_contracts_dict['strike'] < buy_contracts_dict['strike'], sell_contracts_dict['strike'], buy_contracts_dict['strike'])
					sell_strike = float(sell_contracts_dict['strike'])
					buy_strike = float(buy_contracts_dict['strike'])

					combin_contract_dict['return_on_invest'] = (sell_bid - buy_ask) / (sell_strike+0.00000001)
					combin_contract_dict['bid'] = sell_bid
					combin_contract_dict['ask'] = buy_ask
					combin_contract_dict['risk_max'] = (buy_strike - sell_strike + sell_bid - buy_ask) / (sell_strike+0.00000001)
					#print (sell_bid, buy_ask, sell_strike, combin_contract_dict['return_on_invest'])
					#print (str(combin_contract_dict['return_on_invest'])=='nan', str(combin_contract_dict['risk_max'])=='nan')
					if str(combin_contract_dict['return_on_invest'])=='nan' or \
						str(combin_contract_dict['risk_max'])=='nan' or \
						combin_contract_dict['return_on_invest'] < self.PCS_return_on_invest:
						continue
					#min_value_delta = (sell_strike - buy_strike) if (sell_strike - buy_strike) < min_value_delta else min_value_delta
					#if combine_contract_delta_value < (sell_strike - buy_strike):
					#	continue
					if (buy_strike / sell_strike) < self.combine_contract_ratio:
						continue
					
					combin_contract_dict['sell_contractSymbol'] = copy.deepcopy(sell_contracts_dict['contractSymbol'][0])
					combin_contract_dict['buy_contractSymbol'] = copy.deepcopy(buy_contracts_dict['contractSymbol'][0])
					combin_contract_dict['sell_strike_date'] = copy.deepcopy(sell_contracts_dict['date'][0])
					combin_contract_dict['buy_strike_date'] = copy.deepcopy(buy_contracts_dict['date'][0])
					combin_contract_dict['sell_strike_price'] = copy.deepcopy(sell_contracts_dict['strike'][0])
					combin_contract_dict['buy_strike_price'] = copy.deepcopy(buy_contracts_dict['strike'][0])

					combin_contract_dict['string'] = sell_contracts_dict['put_string']
					combin_contract_dict_temp = copy.deepcopy(combin_contract_dict)
					PCS_combin_contract_list.append(combin_contract_dict_temp)
			#print ('PCS_combin_contract_list', PCS_combin_contract_list)
			return PCS_combin_contract_list

		# CCS=SC+BC, the strike of SC need to < BC
		if contract_type == 'call':
			for sell_contracts_dict in sell_contracts_list:
				for buy_contracts_dict in buy_contracts_list:
					combin_contract_dict = {'sell_contractSymbol': -1, \
											'buy_contractSymbol': -1, \
											'return_on_invest': -1, \
											'risk_max': -1, \
											'string': -1, \
											'sell_strike_date': -1, \
											'buy_strike_date': -1, \
											'sell_strike_price': -1, \
											'buy_strike_price': -1, \
											'contract_type': contract_type, \
											'lasted_close': sell_contracts_dict['lasted_close']}
					sell_bid = float(sell_contracts_dict['bid'])
					buy_ask = float(buy_contracts_dict['ask'])
					#print (sell_bid, sell_contracts_dict['strike'], buy_ask, buy_contracts_dict['strike'])
					if sell_contracts_dict['strike'] >= buy_contracts_dict['strike']:
						continue
					if sell_bid <= buy_ask:
						continue
					if sell_contracts_dict['lasted_close']*self.sc_close_ratio < sell_contracts_dict['strike']:
						continue
					sell_strike = float(sell_contracts_dict['strike'])
					buy_strike = float(buy_contracts_dict['strike'])

					combin_contract_dict['return_on_invest'] = (sell_bid - buy_ask) / (sell_strike+0.00000001)
					combin_contract_dict['bid'] = sell_bid
					combin_contract_dict['ask'] = buy_ask
					combin_contract_dict['risk_max'] = (buy_strike - sell_strike + sell_bid - buy_ask) / (sell_strike+0.00000001)
					if str(combin_contract_dict['return_on_invest'])=='nan' or \
						str(combin_contract_dict['risk_max'])=='nan' or \
						combin_contract_dict['return_on_invest'] < self.CCS_return_on_invest:
						continue
					#min_value_delta = (buy_strike - sell_strike) if (buy_strike - sell_strike) < min_value_delta else min_value_delta
					#if combine_contract_delta_value < (buy_strike - sell_strike):
					#	continue
					if (sell_strike / buy_strike) < self.combine_contract_ratio:
						continue

					combin_contract_dict['sell_contractSymbol'] = copy.deepcopy(sell_contracts_dict['contractSymbol'][0])
					combin_contract_dict['buy_contractSymbol'] = copy.deepcopy(buy_contracts_dict['contractSymbol'][0])
					combin_contract_dict['sell_strike_date'] = copy.deepcopy(sell_contracts_dict['date'][0])
					combin_contract_dict['buy_strike_date'] = copy.deepcopy(buy_contracts_dict['date'][0])
					combin_contract_dict['sell_strike_price'] = copy.deepcopy(sell_contracts_dict['strike'][0])
					combin_contract_dict['buy_strike_price'] = copy.deepcopy(buy_contracts_dict['strike'][0])
					combin_contract_dict['string'] = sell_contracts_dict['call_string']
					combin_contract_dict_temp = copy.deepcopy(combin_contract_dict)
					CCS_combin_contract_list.append(combin_contract_dict_temp)
		return CCS_combin_contract_list

	def output_report(self, stock_name, options_file_path, options_com_order_csv_path, result_all):
		lasted_date = list(result_all['moving_average'].keys())[0]
		lasted_close = float(result_all['moving_average'][lasted_date]['close'])
		lasted_situation_type = result_all['moving_average'][lasted_date]['situation_type']
		cow_point_string = ''
		bear_point_string = ''

		#if 'cow' in lasted_situation_type:
		#	for interval_dict in result_all['supported_point']:
		#		if interval_dict['topk_volume'] < 0.5:
		#			break
		#		point_string+='{}/{}/{}  '.format(interval_dict['Interval'], round(interval_dict['topk_volume'], self.interval_value_point), round(1-(float(interval_dict['Interval'].split('_')[1])/lasted_close), self.interval_value_point))
		#else:
		#	for interval_dict in result_all['pressed_point']:
		#		if interval_dict['topk_volume'] < 0.5:
		#			break
		#		point_string+='{}/{}/{}  '.format(interval_dict['Interval'], round(interval_dict['topk_volume'], self.interval_value_point), round(1-(float(interval_dict['Interval'].split('_')[0])/lasted_close), self.interval_value_point))

		# SP:	1-(point/close)越大，closing跟point越遠
		for interval_dict in result_all['supported_point']:
			if interval_dict['topk_volume'] < self.supported_point_rate_thre:
				break
			cow_point_string+='{}/{}/{}  '.format(interval_dict['Interval'], round(interval_dict['topk_volume'], self.interval_value_point), round(1-(float(interval_dict['Interval'].split('_')[1])/lasted_close), self.interval_value_point))
		
		# BP:	1-(point/close)越小，closing跟point越遠
		for interval_dict in result_all['pressed_point']:
			if interval_dict['topk_volume'] < self.pressed_point_rate_thre:
				break
			bear_point_string+='{}/{}/{}  '.format(interval_dict['Interval'], round(interval_dict['topk_volume'], self.interval_value_point), round(1-(float(interval_dict['Interval'].split('_')[0])/lasted_close), self.interval_value_point))

#		'''
		#print (options_file_path)
		#assert False
		with open(options_file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['type', 'date', 'contractSymbol', 'strike', 'bid', \
				'ask', 'bid/strike', 'vol', 'lasted_closing', 'interval / topk% / 1-(point/close)', \
				'change', 'MA5', 'MA20', 'MA40', 'MA80', 'MA40_state(keep)', \
				'MA80_state(keep)', 'situation_type', 'k', 'd'])
			
			try:
				stock_ticker = yf.Ticker(stock_name)
				tmp = stock_ticker.options
			except:
				print ('fail in {}'.format(stock_name))
				return {}, False

			for date in stock_ticker.options:
				for index, opts in enumerate(stock_ticker.option_chain(date)):
					typ = 'call' if index == 0 else 'put'
					point_string = bear_point_string if index == 0 else cow_point_string
					opts_dict = opts.to_dict()
					for idx in opts_dict['contractSymbol'].keys():
						#opt = opts_dict[key][idx]
						writer.writerow([typ, date, opts_dict['contractSymbol'][idx], \
							opts_dict['strike'][idx], opts_dict['bid'][idx], opts_dict['ask'][idx], \
							round(opts_dict['bid'][idx]/opts_dict['strike'][idx], self.interval_value_point), opts_dict['volume'][idx], \
							lasted_close, point_string, \
							opts_dict['change'][idx], result_all['moving_average'][lasted_date]['MA5'], \
							result_all['moving_average'][lasted_date]['MA20'], \
							result_all['moving_average'][lasted_date]['MA40'], \
							result_all['moving_average'][lasted_date]['MA80'], \
							'{}_{}'.format(result_all['MA_state_dict']['MA40_state'], result_all['MA_state_dict']['MA40_state_keep']), \
							'{}_{}'.format(result_all['MA_state_dict']['MA80_state'], result_all['MA_state_dict']['MA80_state_keep']), \
							lasted_situation_type, \
							round(result_all['moving_average'][lasted_date]['K'], self.interval_value_point), \
							round(result_all['moving_average'][lasted_date]['D'], self.interval_value_point)])
#							'''

		#print (options_file_path)
		df = pd.read_csv(options_file_path)
		df_shape = df.shape
		type_last = ''
		date_last = ''
		contracts_list = []
		combin_contract_list_all = []
		contract_dict = {'contractSymbol': -1, \
							'bid': -1, \
							'ask': -1, \
							'strike': -1, \
							'lasted_close': lasted_close, \
							}

		for num in range(df_shape[0]):
			row = df[:][num:num+1]
			contract_dict['contractSymbol'] = row['contractSymbol'].values
			contract_dict['date'] = row['date'].values
			contract_dict['bid'] = row['bid'].values
			contract_dict['ask'] = row['ask'].values
			contract_dict['strike'] = row['strike'].values
			contract_dict['put_string'] = cow_point_string
			contract_dict['call_string'] = bear_point_string
			contract_dict['lasted_close'] = lasted_close
			contract_dict = copy.deepcopy(contract_dict)
			contracts_list.append(contract_dict)
			delta_d = self.get_date_diff(row['date'].values[0], dt.today().strftime("%Y-%m-%d"))
			### hard code with parameter ###
			#if delta_d > 300:
			#	continue

			if (row['type'].values != type_last or row['date'].values != date_last):
				#del contracts_list[-1]
				combin_contract_list = self.get_best_combination_contract(contracts_list[:-2], contracts_list[:-2], type_last)
				combin_contract_list_all.append(combin_contract_list)
				#print (combin_contract_list, type_last)
				#print (combin_contract_list)#, row['type'].values, row['date'].values)
				#if not combin_contract_list== []:
				#	assert False
				contracts_list = []
				contracts_list.append(contract_dict)

			type_last = row['type'].values
			date_last = row['date'].values

		return combin_contract_list_all, True


		'''
		with open(options_com_order_csv_path, 'w', newline='') as csvfile:
			good_contract_dict = {	'sell_contract': -1, \
									'buy_contract': -1, \
									'return_on_invest': -1, \
									'risk_max': -1 }
			for date in stock_ticker.options:
				call_contract_dict = stock_ticker.option_chain(date)[0].to_dict()#['contractSymbol']
				put_contract_dict = stock_ticker.option_chain(date)[1].to_dict()#['contractSymbol']

				for put_contract_sell_idx in put_contract_dict['contractSymbol'].keys():
					for put_contract_buy_idx in put_contract_dict['contractSymbol'].keys():
						good_contract_dict['sell_contract'] = put_contract_dict['contractSymbol'][put_contract_sell_idx]
						good_contract_dict['buy_contract'] = put_contract_dict['contractSymbol'][put_contract_buy_idx]
						#print (put_contract_dict['bid'][put_contract_sell_idx])
						#print (type(put_contract_dict['bid'][put_contract_sell_idx]))
						#assert False
						put_sell_bid = float(put_contract_dict['bid'][put_contract_sell_idx])
						put_buy_ask = float(put_contract_dict['ask'][put_contract_buy_idx])
						if put_sell_bid <= put_buy_ask:
							continue
						#print (put_sell_bid)
						put_sell_strike = float(put_contract_dict['strike'][put_contract_sell_idx])
						put_buy_strike = float(put_contract_dict['strike'][put_contract_buy_idx])
						good_contract_dict['return_on_invest'] = (put_sell_bid - put_buy_ask) / (put_sell_strike+0.00000001)
						good_contract_dict['risk_max'] = put_buy_strike - put_sell_strike + put_sell_bid - put_buy_ask
						if str(good_contract_dict['return_on_invest'])=='nan' or \
							str(good_contract_dict['risk_max'])=='nan' or \
							good_contract_dict['return_on_invest'] < self.PCS_return_on_invest:
							continue
						print (good_contract_dict)
						#input('wait')
			#assert False
		'''
# sp/bp 	sc/bc
					



		#self.PCS_clos_suppo_dist = 0.1
		#self.CCS_clos_press_dist = 0.1
		#self.supported_point_rate_thre = 0.5
		#self.pressed_point_rate_thre = 0.5
		#self.PCS_return_on_invest = 0.03
		#self.CCS_return_on_invest = 0.03

					#print (opts_dict)
		#input('wait')
		
# type date contractSymbol strike bid ask bid/strike vol  Change MA5 MA20 MA40 MA80 MA40_state MA80_state k d

			

			# 寫入一列資料


			# 寫入另外幾列資料
			#writer.writerow(['令狐沖', 175, 60])

	def get_stock_value(self, csv_path, stock_tech_idx_dict, m=1500):
		"""
		function: read closing value
			input:
				csv_path: the path of csv that downloading from yahoo finance
				m: how many days do you want
				stock_tech_idx_dict
			output:
				stock_tech_idx_dict:
				{
					'20191010': {'Close': xxx, 'High': xxx, 'Low': xxx},
					'20191011': {'Close': xxx, 'High': xxx, 'Low': xxx},
					'20191012': {'Close': xxx, 'High': xxx, 'Low': xxx},
				}
		"""
		with open(csv_path, 'r') as file_read:
			for line in file_read.readlines()[-m:]:
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date, Open, High, Low, Close, Adj_Close, Volume = line[0], line[1], line[2], line[3], line[4], line[5], (line[6].strip('\n'))
				if Open == 'null' or High == 'null' or Low == 'null' or Close == 'null' or Volume == 'null':
					Open, High, Low, Close, Volume = Open_last, High_last, Low_last, Close_last, Volume_last
				stock_tech_idx_dict[Date] = {'Close': float(Close),
											 'High': float(High),
											 'Low': float(Low),
											 'MA':  -1,
											 'RSI':  -1,
											 'D': -1,
											 'MACD': -1,
											 'Supported_point': {}}
				Open_last, High_last, Low_last, Close_last, Volume_last = Open, High, Low, Close, Volume
			return stock_tech_idx_dict

	@staticmethod
	def get_date_num(Date):
		return int(Date.split('-')[0])*10000+int(Date.split('-')[1])*100+int(Date.split('-')[2])*1
	
	@staticmethod
	def sort_by_value(d): 
		items=d.items() 
		backitems=[[v[1],v[0]] for v in items] 
		backitems.sort(reverse=True)
		d_out = {}
		for i in range(0,len(backitems)):
			d_out[backitems[i][1]] = d[backitems[i][1]]
		return d_out

	@staticmethod
	def multiply_close_interval(sup_pnt_dict_final, close_interval, interval_value_point, valid_percentage_pnt_threthod):
		d = {}
		first_flag = True
		for sup_dict_key in sup_pnt_dict_final.keys():
			if first_flag:
				value_max = sup_pnt_dict_final[sup_dict_key]
				first_flag = False
			if (sup_pnt_dict_final[sup_dict_key] / (value_max+0.0001)) > valid_percentage_pnt_threthod:
				d[round(sup_dict_key*close_interval, interval_value_point)] = round(sup_pnt_dict_final[sup_dict_key] / value_max, 2)
			#d[round(sup_dict_key*close_interval, interval_value_point)] = sup_pnt_dict_final[sup_dict_key]
		return d

	def process_pnt_list_to_interval(self, support_list, sup_pnt_close_interval, close_interval, interval_value_point, valid_percentage_pnt_threthod):
		sup_pnt_dict_final = {}
		for sup_pnt in support_list:
			sup_pnt_interval_num = sup_pnt['Close']//close_interval if sup_pnt['Close']//close_interval < sup_pnt_close_interval else sup_pnt_close_interval
			if sup_pnt_interval_num in sup_pnt_dict_final.keys():
				sup_pnt_dict_final[sup_pnt_interval_num] += sup_pnt['Volume_sum']
			else:
				sup_pnt_dict_final[sup_pnt_interval_num] = sup_pnt['Volume_sum']
		sup_pnt_dict_final = self.sort_by_value(sup_pnt_dict_final)
		sup_pnt_dict_final = self.multiply_close_interval(sup_pnt_dict_final, close_interval, interval_value_point, valid_percentage_pnt_threthod)
		return sup_pnt_dict_final

	@staticmethod
	def find_min_idx_in_interval(temp_list, idx, min_pass, min_next, stock_dict, stock_date_list):
		#Input:
		#	temp_list: the close_list from 5 days ago ~ 5 days next
		#	idx: main idx(today's idx)
		#	max & min: the max & min close from 5 days ago ~ 5 days next
		#Output:
		#	max & min idx
		stock_close_volume_sum = 0
		start = temp_list.index(min_pass)
		end = temp_list.index(min_next)
		for index in range(start, end+1):
			stock_close_volume_sum+=temp_list[index]*stock_dict[stock_date_list[index]]['Volume']
			#print ('find_min_idx_in_interval', stock_close_volume_sum)
		return stock_close_volume_sum

	@staticmethod
	def find_max_idx_in_interval(temp_list, idx, max_pass, max_next, stock_dict, stock_date_list):
		#Input:
		#	temp_list: the close_list from 5 days ago ~ 5 days next
		#	idx: main idx(today's idx)
		#	max & min: the max & min close from 5 days ago ~ 5 days next
		#Output:
		#	max & min idx
		stock_close_volume_sum = 0
		start = temp_list.index(max_pass)
		end = temp_list.index(max_next)
		for index in range(start, end+1):
			stock_close_volume_sum+=temp_list[index]*stock_dict[stock_date_list[index]]['Volume']
			#print ('find_max_idx_in_interval', stock_close_volume_sum)
		return stock_close_volume_sum

	@staticmethod
	def get_interval_volume_sum(close_list, volume_list, idx, max_pass, max_next, stock_date_list):
		#Input:
		#	temp_list: the close_list from 5 days ago ~ 5 days next
		#	idx: main idx(today's idx)
		#	max & min: the max & min close from 5 days ago ~ 5 days next
		#Output:
		#	max & min idx
		
		stock_volume_sum = 0
		start = close_list.index(max_pass)
		end = close_list.index(max_next)
		for index in range(start, end+1):
			stock_volume_sum+=volume_list[index]
		return stock_volume_sum

	@staticmethod
	def combine_pnt(stock_tech_idx_dict, pnt_dict_final_all, pnt_type):
		if pnt_type == 'Supported_point':
			for date in stock_tech_idx_dict.keys():
				stock_tech_idx_dict[date]['Supported_point'] = pnt_dict_final_all[date]
		elif pnt_type == 'Pressed_point':
			for date in stock_tech_idx_dict.keys():
				stock_tech_idx_dict[date]['Pressed_point'] = pnt_dict_final_all[date]
		else:
			assert False, 'wrong with pnt_type: {} in combine_pnt()'.format(pnt_type)
		return stock_tech_idx_dict

	def get_supported_point(self, file_path, stock_tech_idx_dict, sup_pnt_close_interval=100, valid_percentage_sup_pnt_threthod=0.5):
		# step1 先跑5年，記錄最大累積成交量支撐點（sup_pnt_max）
		# step2 從第6年的第一開始，繼續找支撐點，一旦支撐點形成，先看該支撐點的價格跟其他支撐點的價格距離近不近，如果近就合併(update sup_pnt_dict)
		# sup_pnt_dict = {					sup_pnt_dict = {
		#	'23.5': volume1    -> 			'23.5': volume1,
		# }									'27.5': volume2
		#		 							}
		# step3 找到目前的close_max，並算區間
		# step4 將sup_pnt_dict的volume轉換成百分比 if 有新的支撐點
		# sup_pnt_percentage_dict = {				sup_pnt_percentage_dict = {
		#	'23.5_24.5': 80%	 			->			'23.5_24.5': 80%,
		# }												'26.5_27.5': 74%
		#		 									}
		# step5 將sup_pnt_dict的百分比情況update到stock_tech_idx_dict
		# stock_tech_idx_dict = {									sup_pnt_percentage_dict = {
		#	'2002-11-16': {'sup_pnt': {'23.5_24.5': 80%}}	 ->			'2002-11-16': {'sup_pnt': {'23.5_24.5': 80%}},
		# }																'2004-11-16': {'sup_pnt': {'26.5_27.5': 74%}}
		#		 													}


		first_date = (list(stock_tech_idx_dict.keys())[0])
		first_date_num = self.get_date_num(first_date)
		#assert False
		stock_dict_sum = {'topk_vol':[],'supported_point':{},'pressed_point':{},\
							'moving_average':{}, 'MA_state_dict':{}, 'KD':{}}
		#stock_dict_sum = {'moving_average':{}}
		stock_dict = {}
		press_list = []
		count = 0
		interval_value_point = self.interval_value_point
		sup_pnt_dict_final_all = {}
		Open_last, High_last, Low_last, Close_last, Volume_last = 0, 0, 0, 0, 0
		stock_close_list_temp = []
		stock_volume_list_temp = []
		stock_date_list_temp = []
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				
				#count+=1
				#if count < 12085 or count > 12095:#or count > 13500:
				#	continue
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date, Open, High, Low, Close, Adj_Close, Volume = line[0], line[1], line[2], line[3], line[4], line[5], (line[6].strip('\n'))
				#print (Open, Volume)
				if Open == 'null' or High == 'null' or Low == 'null' or Close == 'null' or Volume == 'null':
					Open, High, Low, Close, Volume = Open_last, High_last, Low_last, Close_last, Volume_last
				if self.get_date_num(Date) < first_date_num:
					continue
				stock_close_list_temp.append(float(Close))
				stock_volume_list_temp.append(int(Volume))
				stock_date_list_temp.append(Date)
				Open_last, High_last, Low_last, Close_last, Volume_last = Open, High, Low, Close, Volume

		#print (len(stock_date_list), stock_date_list[0])

		#round(self.interval_value*(num+1), interval_value_point)
		pass_drop_rate = 0.1
		next_drop_rate = 0.1
		close_max = -1
		for idx_temp, Close_temp in enumerate(stock_close_list_temp):
			support_list = []
			sup_pnt_dict = {}
			stock_close_list = stock_close_list_temp[0:idx_temp+1]
			stock_date_list = stock_date_list_temp[0:idx_temp+1]
			stock_volume_list = stock_volume_list_temp[0:idx_temp+1]
			for idx, Close in enumerate(stock_close_list):
				close_max = Close if Close > close_max else close_max
				close_interval = round((close_max / sup_pnt_close_interval), interval_value_point)

				if idx < self.period_days or idx+self.period_days > len(stock_close_list):
					continue

				Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
				if Close >= Close_five_days_pass_min:
					continue
				Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
				if Close > Close_five_days_pass_max*(1-pass_drop_rate):
					continue
				Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
				if Close > Close_five_days_next_max*(1-next_drop_rate):
					continue
				Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
				if Close >= Close_five_days_next_min:
					continue

				Volume_sum = self.get_interval_volume_sum(stock_close_list[idx-self.period_days:idx+1+self.period_days], \
												stock_volume_list[idx-self.period_days:idx+1+self.period_days], \
												idx, Close_five_days_pass_max, Close_five_days_next_max, \
												stock_date_list)

				support_dict = {'Date': stock_date_list[idx],
								'Volume_sum': Volume_sum,
								'Close': Close,
								#'Close_list': stock_close_list[idx-self.period_days:idx+1+self.period_days],
								#'Close_five_days_pass_max': Close_five_days_pass_max,
								#'Close_five_days_next_max': Close_five_days_next_max,
								}
				#Volume_Value_max = Close*stock_dict[stock_date_list[idx]]['Volume'] if Close*stock_dict[stock_date_list[idx]]['Volume'] > Volume_Value_max else Volume_Value_max
				#Volume_max = stock_dict[stock_date_list[idx]]['Volume'] if stock_dict[stock_date_list[idx]]['Volume'] > Volume_max else Volume_max
				support_list.append(support_dict)
			sup_pnt_dict_final = self.process_pnt_list_to_interval(support_list, sup_pnt_close_interval, close_interval, interval_value_point, valid_percentage_sup_pnt_threthod)
			sup_pnt_dict_final_all[stock_date_list_temp[idx_temp]] = copy.deepcopy(sup_pnt_dict_final)
		stock_tech_idx_dict = self.combine_pnt(stock_tech_idx_dict, sup_pnt_dict_final_all, 'Supported_point')
		return stock_tech_idx_dict

	def get_pressed_point(self, file_path, stock_tech_idx_dict, press_pnt_close_interval=100, valid_percentage_press_pnt_threthod=0.5):
		first_date = (list(stock_tech_idx_dict.keys())[0])
		first_date_num = self.get_date_num(first_date)

		interval_value_point = self.interval_value_point
		press_pnt_dict_final_all = {}
		Open_last, High_last, Low_last, Close_last, Volume_last = 0, 0, 0, 0, 0
		stock_close_list_temp = []
		stock_volume_list_temp = []
		stock_date_list_temp = []
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date, Open, High, Low, Close, Adj_Close, Volume = line[0], line[1], line[2], line[3], line[4], line[5], (line[6].strip('\n'))
				#print (Open, Volume)
				if Open == 'null' or High == 'null' or Low == 'null' or Close == 'null' or Volume == 'null':
					Open, High, Low, Close, Volume = Open_last, High_last, Low_last, Close_last, Volume_last
				if self.get_date_num(Date) < first_date_num:
					continue
				stock_close_list_temp.append(float(Close))
				stock_volume_list_temp.append(int(Volume))
				stock_date_list_temp.append(Date)
				Open_last, High_last, Low_last, Close_last, Volume_last = Open, High, Low, Close, Volume

		pass_drop_rate = 0.1
		next_drop_rate = 0.1
		close_max = -1
		valid_percentage_press_pnt_threthod = 0.5
		for idx_temp, Close_temp in enumerate(stock_close_list_temp):
			press_list = []
			stock_close_list = stock_close_list_temp[0:idx_temp+1]
			stock_date_list = stock_date_list_temp[0:idx_temp+1]
			stock_volume_list = stock_volume_list_temp[0:idx_temp+1]
			for idx, Close in enumerate(stock_close_list):
				close_max = Close if Close > close_max else close_max
				close_interval = round((close_max / press_pnt_close_interval), interval_value_point)

				if idx < self.period_days or idx+self.period_days > len(stock_close_list):
					continue

				Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
				if Close <= Close_five_days_pass_max:
					continue
				Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
				if Close < Close_five_days_pass_min*(1+pass_drop_rate):
					continue
				Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
				if Close < Close_five_days_next_min*(1+next_drop_rate):
					continue
				Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
				if Close < Close_five_days_next_max:
					continue

				Volume_sum = self.get_interval_volume_sum(stock_close_list[idx-self.period_days:idx+1+self.period_days], \
												stock_volume_list[idx-self.period_days:idx+1+self.period_days], \
												idx, Close_five_days_pass_max, Close_five_days_next_max, \
												stock_date_list)

				press_dict = {'Date': stock_date_list[idx],
								'Volume_sum': Volume_sum,
								'Close': Close,
								#'Close_list': stock_close_list[idx-self.period_days:idx+1+self.period_days],
								#'Close_five_days_pass_max': Close_five_days_pass_max,
								#'Close_five_days_next_max': Close_five_days_next_max,
								}
				#Volume_Value_max = Close*stock_dict[stock_date_list[idx]]['Volume'] if Close*stock_dict[stock_date_list[idx]]['Volume'] > Volume_Value_max else Volume_Value_max
				#Volume_max = stock_dict[stock_date_list[idx]]['Volume'] if stock_dict[stock_date_list[idx]]['Volume'] > Volume_max else Volume_max
				press_list.append(press_dict)
			press_pnt_dict_final = self.process_pnt_list_to_interval(press_list, press_pnt_close_interval, close_interval, interval_value_point, valid_percentage_press_pnt_threthod)
			press_pnt_dict_final_all[stock_date_list_temp[idx_temp]] = copy.deepcopy(press_pnt_dict_final)
		stock_tech_idx_dict = self.combine_pnt(stock_tech_idx_dict, press_pnt_dict_final_all, 'Pressed_point')
		return stock_tech_idx_dict

	def get_KD(self, csv_path, stock_tech_idx_dict, nBin=5, nKD=9, m=1500):
		"""
		function: KD
			input:
				csv_path: the path of csv that downloading from yahoo finance
				stock_tech_idx_dict: 
				nBin: how many part do you want to split
				nKD: 
				m: how many days do you want
			output:
				stock_tech_idx_dict:
				{
					'20191010': {'D': 1~5},
					'20191011': {'D': 1~5},
					'20191012': {'D': 1~5},
				}
				1:0~20
				2:21~40
				...
				...
				...
		"""
		K_old, D_old = 0.0, 0.0
		tmp_high_price_list,  tmp_low_price_list = [], []
		for date in stock_tech_idx_dict.keys():
			tmp_high_price_list.append(stock_tech_idx_dict[date]['High'])
			tmp_low_price_list.append(stock_tech_idx_dict[date]['Low'])
			if len(tmp_high_price_list) == nKD and len(tmp_low_price_list) == nKD:
				n_stock_low = min(tmp_low_price_list)
				n_stock_high = max(tmp_high_price_list)
				close = stock_tech_idx_dict[date]['Close']
				RSV = 100.0 * ((close-n_stock_low)/(n_stock_high-n_stock_low+0.00000001))
				K_new = (2 * K_old / 3) + (RSV / 3)
				D_new = (2 * D_old / 3) + (K_new / 3)
				stock_tech_idx_dict[date]['D'] = D_new // (100/nBin)
				K_old, D_old = K_new, D_new
				tmp_high_price_list.pop(0)
				tmp_low_price_list.pop(0)

		return stock_tech_idx_dict

	def output_tech_idx(self, tech_idx_path, stock_tech_idx_dict):
		with open(tech_idx_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(['idx', 'date', 'Close', 'MA', 'MACD', 'D', 'RSI', 'Supported_point', 'Pressed_point'])
			for index, date in enumerate(stock_tech_idx_dict.keys()):
				#print (index)
				#print (date)
				writer.writerow([index, date, stock_tech_idx_dict[date]['Close']\
					, stock_tech_idx_dict[date]['MA'], stock_tech_idx_dict[date]['MACD']\
					, stock_tech_idx_dict[date]['D'], stock_tech_idx_dict[date]['RSI']\
					, json.dumps(stock_tech_idx_dict[date]['Supported_point'])\
					, json.dumps(stock_tech_idx_dict[date]['Pressed_point'])])

	def get_MA(self, CSV, stock_tech_idx_dict, Total_day=10*250, percent=1): #Slew_keep_day, 
		'''
		Input:
		CSV: Yahoo API stock history
		Total_Day: MA's days caculatation
		percent: if smaller this percent, which is unknow status

		Output:
		1=Bull_big: MA5 > MA4 > MA40 > MA80
		2=Bull_Samll: MA40 > MA80
		3=Bull_Samll_5<40: MA40 > MA80, MA40 > MA5
		4=kink_P: else & MA80 increase 3 days
		5=Bear_big: MA5 < MA4 < MA40 < MA80
		6=Bear_Samll: MA40 < MA80
		7=Bear_Samll_5>40: MA40 > MA80, MA40 > MA5
		8=kink_n: else & MA80 decrease 3 days
		9=kink: else

		MA5=avg(5 close days)
		MA4=avg(4 MA5 days)
		FMA40=Weighted moving average: close[40-n]*(40-n)/(40*(40+1)/2)
		FMA80=Weighted moving average: FMA40[80-n]*(80-n)/(80*(80+1)/2)
		'''

		with open(CSV,'r') as f_r:
			price_history = f_r.readlines()
			strat_row=len(price_history)-Total_day+1-120 # >120 is MA80 effective data
			Loop_T=Total_day+120-1
			if strat_row<1: 
				strat_row=1
				Loop_T=len(price_history)-1
			#initialize
			MA5=0
			MA4=0
			MA40=0
			MA80=0
			sum_n40=0
			sum_n80=0
			#=============================
			b_g4=percent/4/100+1
			b_g40=percent/2/100+1
			b_g80=percent/100+1
			s_g4=1-percent/4/100
			s_g40=1-percent/2/100
			s_g80=1-percent/100
			#=============================
			summary={}
			MA_temp1={}
			MA_temp3={}
			lasted_close = 0
			for i in range (0,Loop_T):
				MA_temp2={}
				Date=price_history[strat_row].replace('\n','').split(',')[0]
				
				Close=price_history[strat_row].replace('\n','').split(',')[5]
				if Close == 'null':
					Close = lasted_close
				MA_temp2['Close']=Close
				MA_temp2['Date']=Date
				# ========================MA5========================
				try:
				    MA5 = float(MA5) + float(Close)
				except:
					print (Date, MA5, Close, CSV)
				MA_temp2['MA5']=0
				MA_temp1[i]=MA_temp2
				if i>= 4:
					MA_temp1[i]['MA5']= round(float(MA5)/5,2)
					MA5=float(MA5)-float(MA_temp1[i-4]['Close'])
				# ========================MA4========================
				MA4 = float(MA4) + float(MA_temp1[i]['MA5'])
				MA_temp2['MA4']=0
				MA_temp1[i]=MA_temp2
				if i>= 3:
					MA_temp1[i]['MA4']= round(float(MA4)/4,2)
					MA4=float(MA4)-float(MA_temp1[i-3]['MA5'])
				# ========================FMA40========================
				MA40 = float(MA40) + float(Close)
				MA_temp2['MA40']=0
				MA_temp1[i]=MA_temp2
				if i>= 39:
					n=0
					for m in range (0,40):
						try:
							sum_n40=float(sum_n40)+float(MA_temp1[i-n]['Close'])*(40-n)/(40*(40+1)/2)
						except:
							break
						n=n+1
					MA_temp1[i]['MA40']= round(sum_n40,2)
					sum_n40=0
				# ========================FMA80========================
				MA80 = float(MA80) + float(MA_temp1[i]['MA40'])
				MA_temp2['MA80']=0
				MA_temp1[i]=MA_temp2
				if i>= 79:
					n=0
					for m in range (0,80):
						try:
							sum_n80=float(sum_n80)+float(MA_temp1[i-n]['MA40'])*(80-n)/(80*(80+1)/2)
						except:
							break
						n=n+1
					MA_temp1[i]['MA80']= round(sum_n80,2)
					sum_n80=0
				strat_row=strat_row+1
				# ========================MA summary========================
				MA_5=float(MA_temp1[i]['MA5']) #green
				MA_4=float(MA_temp1[i]['MA4']) #red
				MA_40=float(MA_temp1[i]['MA40']) #white
				MA_80=float(MA_temp1[i]['MA80']) # blue
				MA_temp2['MA_sum']=0
				MA_temp1[i]=MA_temp2

				if MA_5 > MA_4*b_g4 and MA_4 > MA_40*b_g40 and MA_40 > MA_80*b_g80:# 	
					MA_temp1[i]['MA_sum'] =1 # 'Bull-Big'
				elif MA_5 < MA_4*s_g4 and MA_4 < MA_40*s_g40 and MA_40 < MA_80*s_g80:# 	
					MA_temp1[i]['MA_sum'] =5 # 'Bear-Big'
				elif MA_40 > MA_80*b_g80 and MA_5 < MA_40*s_g40:# 
					MA_temp1[i]['MA_sum'] =3 # 'Bull-small_5<40'
				elif MA_40 < MA_80*s_g80 and MA_5 > MA_40*b_g40:# 	
					MA_temp1[i]['MA_sum'] =7 # 'Bear-small_5>40'
				elif MA_40 > MA_80*b_g80:# 
					MA_temp1[i]['MA_sum'] =2 # 'Bull-small'
				elif MA_40 < MA_80*s_g80:# 	
					MA_temp1[i]['MA_sum'] =6 # 'Bear-small'
				else:
					try:
						if MA_temp1[i]['MA80']>MA_temp1[i-1]['MA80'] and MA_temp1[i-1]['MA80']>MA_temp1[i-2]['MA80']:
							MA_temp1[i]['MA_sum'] =4 # 'kink_P'
						elif MA_temp1[i]['MA80']<MA_temp1[i-1]['MA80'] and MA_temp1[i-1]['MA80']<MA_temp1[i-2]['MA80']:
							MA_temp1[i]['MA_sum'] =8 # 'kink_n'
						else:
							MA_temp1[i]['MA_sum'] =9 # 'kink'
					except:
							MA_temp1[i]['MA_sum'] =9 # 'kink'					
				
				sum_temp={}
				sum_temp['MA']=MA_temp1[i]['MA_sum']
				summary[Date]=sum_temp
				#MA_temp3[Date] = copy.deepcopy(MA_temp2)
				stock_tech_idx_dict[Date]['MA'] = copy.deepcopy(MA_temp2['MA_sum'])
				lasted_close = Close
			#return summary
		return stock_tech_idx_dict

	def get_RSI(self, csv_path, stock_tech_idx_dict, nBin=5, n=6, m=1500):
		"""
		function: RSI
			input:
				csv_path: the path of csv that downloading from yahoo finance
				stock_tech_idx_dict: 
				nBin: how many part do you want to split
				n: average days 
				m: how many days do you want
			output:
				stock_tech_idx_dict:
				{
					'20191010': {'RSI': 1~5},
					'20191011': {'RSI': 1~5},
					'20191012': {'RSI': 1~5},
				}
				1:0~20
				2:21~40
				...
				...
				...
		"""
		tmp_up_price_list, tmp_down_price_list, tmp_mv_down_price_list, tmp_mv_up_price_list = [], [], [], []
		fisrt_flag=True
		for date in stock_tech_idx_dict.keys():
			if fisrt_flag:
				close_last = stock_tech_idx_dict[date]['Close']
				fisrt_flag=False
				continue
			if stock_tech_idx_dict[date]['Close'] > close_last:
				tmp_up_price_list.append(abs(stock_tech_idx_dict[date]['Close'] - close_last))
				tmp_down_price_list.append(0)
			elif stock_tech_idx_dict[date]['Close'] < close_last:
				tmp_up_price_list.append(0)
				tmp_down_price_list.append(abs(stock_tech_idx_dict[date]['Close'] - close_last))
			else:
				tmp_up_price_list.append(0)
				tmp_down_price_list.append(0)
			close_last = stock_tech_idx_dict[date]['Close']
			if len(tmp_up_price_list) == n and len(tmp_down_price_list) == n:
				mv_down_price = sum(tmp_down_price_list) / n
				mv_up_price = sum(tmp_up_price_list) / n
				RSI = (100 * mv_up_price) / (mv_up_price + mv_down_price + 0.001)
				stock_tech_idx_dict[date]['RSI'] = RSI // (100/nBin)
				tmp_up_price_list.pop(0)
				tmp_down_price_list.pop(0)
		return stock_tech_idx_dict

	def get_MACD(self, CSV, stock_tech_idx_dict, Total_day_MACD, MACD_short, MACD_long, MACD_signallength): #Slew_keep_day, 
		
		'''		
		show percentage of MACD, the purpose is compare with K'D' in the same scale.

		0~20=0
		20~40=1
		40~60=2
		60~80=3
		80~100=4
		'''
		Total_day=Total_day_MACD*1
		with open(CSV,'r') as f_r:
			price_history = f_r.readlines()
			strat_row=int(len(price_history)-Total_day+1-Total_day/5) # >Total_day/5 is MACD effective data
			Loop_T=int(Total_day+Total_day/5-1)
			if strat_row<1: 
				strat_row=1
				Loop_T=len(price_history)-1
			#initialize
			summary={}
			MACD_temp1={}
			MACD_temp3={}
			# j=strat_row
			lasted_close = 0
			for i in range (0,Loop_T):
				MACD_temp2={}
				Date=price_history[strat_row].replace('\n','').split(',')[0]
				#try: 
				#	Close=price_history[strat_row].replace('\n','').split(',')[5]
				#except: # close=nan
				#	Close=price_history[strat_row-1].replace('\n','').split(',')[5]
				Close=price_history[strat_row].replace('\n','').split(',')[5]
				if Close == 'null':
					Close = lasted_close
				MACD_temp2['Close']=Close
				MACD_temp2['Date']=Date

				MACD_temp1[i]=MACD_temp2

				EMA_short_initial=0
				EMA_long_initial=0
				DEM_initial=0
				if i==0:
					MACD_temp1[i]['EMA_short'] =EMA_short_initial+2/(MACD_short+1)*(float(Close)-EMA_short_initial)  # short_EMA innitial=0
					MACD_temp1[i]['EMA_long'] =EMA_long_initial+2/(MACD_long+1)*(float(Close)-EMA_long_initial)  # long_EMA innitial=0
				else:
					MACD_temp1[i]['EMA_short'] =MACD_temp1[i-1]['EMA_short']+2/(MACD_short+1)*(float(Close)-MACD_temp1[i-1]['EMA_short'])
					MACD_temp1[i]['EMA_long'] =MACD_temp1[i-1]['EMA_long']+2/(MACD_long+1)*(float(Close)-MACD_temp1[i-1]['EMA_long'])

				MACD_temp1[i]['MACD_DIF'] =round(MACD_temp1[i]['EMA_short']-MACD_temp1[i]['EMA_long'],2)
				if i==0:
					MACD_temp1[i]['DEM'] = DEM_initial+2/(MACD_signallength+1)*(MACD_temp1[i]['MACD_DIF']-DEM_initial)
				else:
					MACD_temp1[i]['DEM'] = MACD_temp1[i-1]['DEM']+2/(MACD_signallength+1)*(MACD_temp1[i]['MACD_DIF']-MACD_temp1[i-1]['DEM'])				
				MACD_temp1[i]['OSC'] = round(MACD_temp1[i]['MACD_DIF']-MACD_temp1[i]['DEM'],2)
				
				MACD_temp3[i]=MACD_temp1[i]['MACD_DIF']
				if i>=Total_day/6: #after 1/6 of total row, DIF have more accuracy
				#===============show MACD level
					new_temp3 = {i:MACD_temp3[i] for i in MACD_temp3 if i>=Total_day/6}  # remove dict:key< Total_day/5, avoid rank
					r = {key: rank for rank, key in enumerate(sorted(set(new_temp3.values()), reverse=False), 1)} #get rank 
					MACD_rank={k: r[v] for k,v in new_temp3.items()} #get rank of key
					DIF_max=max(MACD_rank.items(), key=operator.itemgetter(1))[0] 
					DIF_max=MACD_rank[DIF_max] # find max rank
					MACD_temp1[i]['MACD%'] =round(int(MACD_rank[i])/DIF_max*100,2)
				#===============show MACD level	
				if i>=Total_day/5: #only capture after 1/5 of total row, MACD% will be more accuracy
					MACD_per=float(MACD_temp1[i]['MACD%'])
					'''
					0~20=0
					20~40=1
					40~60=2
					60~80=3
					80~100=4
					'''
					if MACD_per>=80:
						MACD_temp1[i]['Range']=4
					elif MACD_per<80 and MACD_per>=60:
						MACD_temp1[i]['Range']=3
					elif MACD_per<60 and MACD_per>=40:
						MACD_temp1[i]['Range']=2
					elif MACD_per<40 and MACD_per>=20:
						MACD_temp1[i]['Range']=1
					else:
						MACD_temp1[i]['Range']=0
					
					summary[Date]=MACD_temp1[i]['Range']
					stock_tech_idx_dict[Date]['MACD'] = copy.deepcopy(MACD_temp1[i]['Range'])
				strat_row=strat_row+1
				lasted_close = Close
			return stock_tech_idx_dict

	def get_supporting_point(self, stock_name, file_path):
		print ('stock_name: {}'.format(stock_name))
		stock_dict_sum = {'topk_vol':[],'supported_point':{},'pressed_point':{},\
							'moving_average':{}, 'MA_state_dict':{}, 'KD':{}}
		#stock_dict_sum = {'moving_average':{}}
		stock_dict = {}
		stock_close_list = []
		stock_low_list = []
		stock_high_list = []
		press_list = []
		stock_date_list = []
		stock_volume_list = []
		count = 0
		interval_value_point = 3
		Open_last, High_last, Low_last, Close_last, Volume_last = 0, 0, 0, 0, 0
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				count+=1
				#if count < 12085 or count > 12095:#or count > 13500:
				#	continue
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date, Open, High, Low, Close, Adj_Close, Volume = line[0], line[1], line[2], line[3], line[4], line[5], (line[6].strip('\n'))
				#print (Open, Volume)
				if Open == 'null' or High == 'null' or Low == 'null' or Close == 'null' or Volume == 'null':
					Open, High, Low, Close, Volume = Open_last, High_last, Low_last, Close_last, Volume_last
				stock_dict[Date] = {'Date': Date,
									'Open': Open,
									'High': High,
									'Low': Low,
									'Close': float(Close),
									'Adj_Close': Adj_Close,
									'Volume': int(Volume)}
				stock_close_list.append(float(Close))
				stock_low_list.append(float(Low))
				stock_high_list.append(float(High))
				stock_volume_list.append(int(Volume))
				stock_date_list.append(Date)
				Open_last, High_last, Low_last, Close_last, Volume_last = Open, High, Low, Close, Volume
		self.interval_value = round(max(stock_close_list) / self.part_num, interval_value_point)
		#print (self.interval_value, max(stock_close_list), self.part_num)
		#print (stock_dict)
		#print (stock_name, 'get_supporting_point')
		topk_volume_list = [0]*self.part_num
		for key in stock_dict_sum.keys():
			if key == 'topk_vol':
				# topk volume
				#topk_volume_list = [0]*self.part_num
				stock_volume_list_tmp = copy.deepcopy(stock_volume_list)

				for num in range(self.top_volume_num):
					max_volume = max(stock_volume_list_tmp)
					stock_volume_list_tmp.remove(max_volume)
					max_idx = stock_volume_list.index(max_volume)
					max_date = stock_date_list[max_idx]
					max_volume_close = stock_close_list[max_idx]
					#topk_volume_list.append({max_date: {'volume': max_volume, \
					#									'close': max_volume_close}})
					#print (int(max_volume_close//(max_volume_close // self.part_num)))
					idx_tmp = int(max_volume_close/(self.interval_value)) if int(max_volume_close/(self.interval_value)) <= len(topk_volume_list)-1 else len(topk_volume_list)-1
					topk_volume_list[idx_tmp] += max_volume
				#print (topk_volume_list)

				stock_dict_sum['topk_vol'] = topk_volume_list
			if key == 'press':
				# press
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue
					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_min*(1+self.difference_rate):
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_max:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_min*(1+self.difference_rate):
						continue
					#print (idx, Close)
					press_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					press_list.append(press_dict)
				#print (press_list)
			if key == 'pressed_point':
				press_list = []
				# calculate supported point
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue

					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_min*(1+self.difference_rate):
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_max:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_min*(1+self.difference_rate):
						continue
					# 在這邊要加總
					#print (idx, Close)
					Volume_Value = self.find_min_idx_in_interval(stock_close_list[idx-self.period_days:idx+1+self.period_days], \
													idx, Close_five_days_pass_min, Close_five_days_next_min, \
													stock_dict, stock_date_list)
					press_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Volume_Value,
									'Volume': stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					press_list.append(press_dict)

				# interval
				Volume_Value_max = -1
				Volume_max = -1
				press_all_dict = {}
				topk_volume_all_dict = {}
				for num in range(self.part_num+3):
					press_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0

				for press_dict_tmp in press_list:
					num = int(press_dict_tmp['Close'] / self.interval_value)
					#print (press_all_dict)
					press_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] \
						+=press_dict_tmp['Volume_Value']
				# normalize press_all_dict
				# first, get Volume_Value_max
				for press_dict_val in press_all_dict.values():
					Volume_Value_max = press_dict_val if press_dict_val > Volume_Value_max else Volume_Value_max
				# second, normalization
				for press_dict_key in press_all_dict.keys():
					press_all_dict[press_dict_key] = press_all_dict[press_dict_key] / float(Volume_Value_max+0.00000001)


				for idx, value in enumerate(topk_volume_list):
					Volume_max = value if value > Volume_max else Volume_max
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						+=value
				for idx, value  in enumerate(topk_volume_list):
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						= topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] / float(Volume_max)

				press_all_list = []

				for key in topk_volume_all_dict.keys():
					if press_all_list == []:
						press_all_list.append({'Interval': key, \
												'Volume_Value': press_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
					else:
						insert_idx = 0
						for press_dict in press_all_list:
							# 現在要加入的press_all_dict[key]要加到idx多少
							if press_dict['topk_volume'] >= topk_volume_all_dict[key]:
								insert_idx += 1
							else:
								break
						press_all_list.insert(insert_idx, {'Interval': key, \
												'Volume_Value': press_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
#												'''
				#print (press_all_list)
				stock_dict_sum['pressed_point'] = press_all_list


			if key == 'supported_point':
				support_list = []
				# calculate supported point
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue

					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close < Close_five_days_pass_min:
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close < Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close < Close_five_days_next_max*1.1:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close < Close_five_days_next_min:
						continue
					#print (idx, Close)
					Volume_Value = self.find_max_idx_in_interval(stock_close_list[idx-self.period_days:idx+1+self.period_days], \
													idx, Close_five_days_pass_max, Close_five_days_next_max, \
													stock_dict, stock_date_list)

					support_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Volume_Value,
									'Volume': stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					#Volume_Value_max = Close*stock_dict[stock_date_list[idx]]['Volume'] if Close*stock_dict[stock_date_list[idx]]['Volume'] > Volume_Value_max else Volume_Value_max
					#Volume_max = stock_dict[stock_date_list[idx]]['Volume'] if stock_dict[stock_date_list[idx]]['Volume'] > Volume_max else Volume_max
					support_list.append(support_dict)

				# interval
				Volume_Value_max = -1
				Volume_max = -1
				support_all_dict = {}
				topk_volume_all_dict = {}
				for num in range(self.part_num+3):
					support_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
				

				for support_dict_tmp in support_list:
					num = int(support_dict_tmp['Close'] / self.interval_value)
					support_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] \
						+=support_dict_tmp['Volume_Value']
				# normalize support_all_dict
				# first, get Volume_Value_max
				for support_dict_val in support_all_dict.values():
					Volume_Value_max = support_dict_val if support_dict_val > Volume_Value_max else Volume_Value_max
				# second, normalization
				for support_dict_key in support_all_dict.keys():
					support_all_dict[support_dict_key] = support_all_dict[support_dict_key] / float(Volume_Value_max+0.00000001)


				for idx, value in enumerate(topk_volume_list):
					Volume_max = value if value > Volume_max else Volume_max
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						+=value
				for idx, value  in enumerate(topk_volume_list):
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						= topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] / float(Volume_max)


				# sort by interval value
				'''
				support_all_list = []
				for key in topk_volume_all_dict.keys():
					support_all_list.append({'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
												'''

				# sort by topk_volume or Volume_Value
#				'''
				support_all_list = []

				for key in topk_volume_all_dict.keys():
					#if support_all_dict[key] == 0:
					#	continue
					if support_all_list == []:
						support_all_list.append({'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
					else:
						insert_idx = 0
						for support_dict in support_all_list:
							# sorted by supported volume * close value
							#if support_dict['Volume_Value'] >= support_all_dict[key]:
							# sorted by topk volume
							# 現在要加入的support_all_dict[key]要加到idx多少
							if support_dict['topk_volume'] >= topk_volume_all_dict[key]:
								insert_idx += 1
							else:
								break
						support_all_list.insert(insert_idx, {'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
#												'''
				#print (support_all_list)
				stock_dict_sum['supported_point'] = support_all_list

			if key == 'moving_average':
#					moving_average: {'2012-02-14': {'type': big_cow,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									'2012-02-1X': {'type': small_bear,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									....}
				MA_dict = {}
				MA_dict_all = {}
				MA_state_dict = {}
				first_enter = True
				MA40_state = 0
				MA80_state = 0
				change_state = False
				MA40_change_state, MA80_change_state = False, False
				for idx in range(len(stock_close_list)-1, len(stock_close_list)-self.ma_days, -1):
					#print (len(stock_close_list)-1, len(stock_close_list)-self.ma_days, -1)
					#print (idx)
					#print (len(stock_close_list), idx, len(stock_close_list)-self.ma_days, self.ma_days)
					close = stock_close_list[idx]
					# 1 2 3 4 5 6 7 8 len=8 [3:8]->[idx-ma+1:idx+1]
					MA5 = round(sum(stock_close_list[idx-5+1:idx+1]) / 5.0, 2)
					MA20 = round(sum(stock_close_list[idx-20+1:idx+1]) / 20.0, 2)
					MA40 = round(sum(stock_close_list[idx-40+1:idx+1]) / 40.0, 2)
					MA80 = round(sum(stock_close_list[idx-80+1:idx+1]) / 80.0, 2)
					#print (MA5, MA20, MA40, MA80)
					situation_type = 'big_cow' if MA5 > MA20 > MA40 > MA80 else 'small_cow' if MA40 > MA80 \
									else 'big_bear' if MA5 < MA20 < MA40 < MA80 else 'small_bear'
					MA_dict = {'situation_type': situation_type, \
								'close': close, \
								'MA5': MA5, \
								'MA20': MA20, \
								'MA40': MA40, \
								'MA80': MA80 }
					MA_dict_all['{}'.format(stock_date_list[idx])] = MA_dict
					
					if first_enter:
						first_enter = False
					else:
						MA40_state = 1 if MA40 > MA40_last else -1
						MA80_state = 1 if MA80 > MA80_last else -1
						if MA_state_dict == {}:
							MA_state_dict = {'MA40_state_keep': 0, 'MA80_state_keep': 0}

						else:
							MA40_change_state = False if ((MA40_state_last == MA40_state) and (MA40_change_state == False)) else True
							MA80_change_state = False if ((MA80_state_last == MA80_state) and (MA80_change_state == False)) else True
							if not MA40_change_state:
								MA_state_dict['MA40_state_keep'] += 1
							else:
								MA40_change_state = True

							if not MA80_change_state:
								MA_state_dict['MA80_state_keep'] += 1
							else:
								MA80_change_state = True
						#try:
						#	print (MA40, MA40_last, MA40_state, MA40_state_last, MA40_change_state)
						#	print (MA80, MA80_last, MA80_state, MA80_state_last, MA80_change_state)
						#	print ((MA40_state_last == MA40_state), (MA40_change_state == False))
						#	input('wait')
						#except:
						#	pass
						MA40_state_last = MA40_state
						MA80_state_last = MA80_state

					MA40_last, MA80_last, = MA40, MA80

				#print (MA_dict_all)
				MA_state_dict['MA40_state'] = MA40_state
				MA_state_dict['MA80_state'] = MA80_state
				stock_dict_sum['moving_average'] = MA_dict_all
				stock_dict_sum['MA_state_dict'] = MA_state_dict


			if key == 'KD':
#				x_list = []
#				y_list = []
#				import numpy as np
#				import pandas as pd
#				import matplotlib.pyplot as plt

				K_old, D_old = 0.0, 0.0
#				yk_list = []
#				yd_list = []
				for idx in range(self.nKD-1, len(stock_close_list)):
					n_stock_low = min(stock_low_list[idx-self.nKD+1:idx+1])
					n_stock_high = max(stock_high_list[idx-self.nKD+1:idx+1])
					close = stock_close_list[idx]
					RSV = 100.0 * ((close-n_stock_low)/(n_stock_high-n_stock_low+0.00000001))
					K_new = (2 * K_old / 3) + (RSV / 3)
					D_new = (2 * D_old / 3) + (K_new / 3)
					K_old, D_old = K_new, D_new
					if stock_date_list[idx] in stock_dict_sum['moving_average'].keys():
						data = stock_date_list[idx]
						stock_dict_sum['moving_average'][data]['K'] = K_new
						stock_dict_sum['moving_average'][data]['D'] = D_new
#					if not (len(stock_close_list)-idx) < 70:
#						continue
#					x_list.append(idx)
#					yk_list.append(K_old)
#					yd_list.append(D_old)
#					x_val = np.asarray(x_list)
#					yk_a = np.asarray(yk_list)
#					yd_a = np.asarray(yd_list)
#		plt.plot(x_val, yk_a)
#		plt.plot(x_val, yd_a)
#		plt.show()

		#print (stock_dict_sum)
		return stock_dict_sum

# 用基本面篩選
# MA 40 80負斜率持續 70天就不要
# 判斷大小牛熊（大牛：MA5>MA20>MA40>MA80、小牛：MA40>MA80）
#  

# csv_type： MA_5 MA_20 MA_40 MA_80 MA_sum 支撐 大量

		# 將value_volume=0的刪除
		# 用將value_volume排序，由大到小
		# 找到前10大量的落點
		# 回測改變period_days、difference_rate、要幾個最大量、
		# 找到support point時抓前後幾天、top k是volume or volume*value的detection rate
		

		#count_list = range(len(stock_date_list))
		#plt.plot(count_list, stock_volume_list)
		#plt.show()


		"""
		import numpy as np
		import pandas as pd
		import matplotlib.pyplot as plt

		x = stock_date_list
		x = np.asarray(range(len(stock_date_list)))
		y_val = np.asarray(stock_close_list)*2000000
		y_vol = np.asarray(stock_volume_list)
		print (x)
		print (y_val)
		plt.plot(x, y_val)
		plt.plot(x, y_vol)
		plt.show()
		"""

#		fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(8, 8))
#		labelled_data = zip((y_val, y_vol), ('value', 'volume'), ('b', 'g'))
#		fig.suptitle('Three Random Trends', fontsize=16)
#
#		for i, ld in enumerate(labelled_data):
#			ax = axes[i]
#			ax.plot(x, ld[0], label=ld[1], color=ld[2])
#			#ax.set_ylabel('Cum. sum')
#			#ax.legend(loc='upper left', framealpha=0.5, prop={'size': 'small'})
#		axes[-1].set_xlabel('Date')
#		plt.show()

	def analysis_statement(self, stock_name):
		stock_dict = finviz.get_stock(stock_name)
		if self.analysis_statement_status == 0:
			return True
		if not stock_dict['Optionable'] == 'Yes':
			#print ('unOptionable')
			return False
		if not 'M' in stock_dict['Avg Volume']:
			#print ('low Volume')
			return False
		if self.analysis_statement_status == 2:
			if '-' in stock_dict['ROE']:
				#print ('-roe')
				return False
			if float(stock_dict['ROE'][:-1]) < 10.0:
				#print ('roe')
				return False
			if '-' in stock_dict['EPS Q/Q']:
				#print (stock_name, 'EPS Q/Q')
				#print ('eps')
				return False
			if '-' in stock_dict['EPS next Q']:
				#print (stock_name, 'EPS next Q')
				#print ('eps2')
				return False
			if '-' in stock_dict['Sales Q/Q']:
				#print (stock_name, 'EPS next Q')
				#print ('eps2')
				return False

		return True


# Optionable
# Avg Volume
# EPS (ttm)
# EPS next Y
# EPS next Q
# EPS this Y
# EPS next 5Y
# EPS past 5Y
# EPS Q/Q
	def analysis_document(self, workers_num, stock_queues):
		"""
		calculating the supporting point and stress point
		"""
		while not stock_queues.empty():
			fail_flag = False
			stock_name = stock_queues.get()
			if not self.analysis_statement(stock_name):
				continue

			sav_stock_csv_path = '{}.csv'.format(os.path.join(self.stock_folder_path, stock_name))
			sav_option_csv_path = '{}.csv'.format(os.path.join(self.option_folder_path, stock_name))
			sav_option_com_order_csv_path = '{}.csv'.format(os.path.join(self.option_com_order_folder_path, stock_name))
			if not os.path.exists(self.option_folder_path):
				os.mkdir(self.option_folder_path)
			if not os.path.exists(self.option_com_order_folder_path):
				os.mkdir(self.option_com_order_folder_path)
			if not os.path.exists(self.techidx_folder_path):
				os.mkdir(self.techidx_folder_path)
			df = self.crawl_price(stock_name)
			if len(df) < self.min_days:
				continue

			result_all = self.get_supporting_point(stock_name, sav_stock_csv_path)
			#continue
			#self.output_report(stock_name, sav_option_csv_path, sav_option_com_order_csv_path, result_all)
			#print (sav_stock_csv_path, sav_option_csv_path, sav_option_com_order_csv_path)
			tech_idx_path = 'techidx/{}.csv'.format(stock_name)

			options_contract_file_path = 'options/{}.csv'.format(stock_name)
			sav_stock_csv_path = '{}.csv'.format(os.path.join(self.stock_folder_path, stock_name))
			options_file_path = '{}.csv'.format(os.path.join(self.option_folder_path, stock_name))
			options_com_order_csv_path = '{}.csv'.format(os.path.join(self.option_com_order_folder_path, stock_name))
			combin_contract_list_all, state_flag = self.output_report(stock_name, options_file_path, options_com_order_csv_path, result_all)
			if not state_flag:
				#print ('continue')
				continue
			self.best_contract(stock_name)
			best_combin_contract_all = self.back_testing(tech_idx_path, options_contract_file_path, combin_contract_list_all)
			print (best_combin_contract_all)

			print ('worker number {}, stock_name is {}'.format(workers_num, stock_name))

#			for date in best_combin_contract_all.keys():


			best_combin_contract_all_json = json.dumps(best_combin_contract_all)
			#print (len(best_combin_contract_all) != 0, len(best_combin_contract_all))
			if len(best_combin_contract_all) != 0:
				with open(options_com_order_csv_path, 'w') as f_w:
					f_w.write(best_combin_contract_all_json)

	@staticmethod
	def crawl_price(stock_id):
		now = int(datetime.datetime.now().timestamp())+86400
		url = "https://query1.finance.yahoo.com/v7/finance/download/" + stock_id + "?period1=0&period2=" + str(now) + "&interval=1d&events=history&crumb=hP2rOschxO0"
		response = requests.post(url)

		with open('stocks/{}.csv'.format(stock_id), 'w') as f:
			f.writelines(response.text)
		try:
			df = pd.read_csv('stocks/{}.csv'.format(stock_id), index_col='Date', parse_dates=['Date'])
		except:
			return []
		return df

class Boss(object):
	def __init__(self, stock_name_list):
		count = 0
		self.stock_queues = queues.Queue(len(stock_name_list), ctx=multiprocessing)
		for stock_name in stock_name_list:
			self.stock_queues.put(stock_name)
		self.workers = []


	def load_config(self, config_path):
		"""
		loading information from configure file
		input:
			the path of configure file
		output:
			self.stock_list: [stock name 1, stock name 2, ....]
			self.period_days: v shape, from 100 to 100*(1-self.difference_rate) in self.period_days days, and 
						100*(1-self.difference_rate) to 100*(1-self.difference_rate)*(1+self.difference_rate)
						in self.period_days days, 100*(1-self.difference_rate) is supporting_point
			self.difference_rate: ↑

		"""

		with open(config_path,'r') as config_file:
			config_lines = config_file.readlines()
			self.stock_folder_path = config_lines[0].strip()
			self.option_folder_path = config_lines[1].strip()
			if not os.path.exists(self.stock_folder_path):
				os.makedirs(self.stock_folder_path)
			self.num_worker = int(config_lines[2].strip())
			self.period_days = int(config_lines[3].strip())
			self.difference_rate = float(config_lines[4].strip())
			self.roe_ttm = float(config_lines[5].strip())

	def hire_worker(self):
		"""
		using multiprocess to process .csv, we will enable self.num_worker thread to process data
		"""
		for i in range(self.num_worker):
			trader = copy.deepcopy(Trader(self.period_days, self.difference_rate, self.stock_folder_path, self.option_folder_path, self.roe_ttm))
			print ('worker {}'.format(i))
			self.workers.append(trader)

	def assign_task(self):
		for i in range(self.num_worker):
			p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			p.start()
			p.join(timeout=0.1)
		#self.workers[0].analysis_document(0, self.stock_queues)

		print ('assign task finish!')


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--config_path', type=str)
	return parser.parse_args()

def main():
	#print (len(get_stock_name_list()))
	#assert False
	param = get_args()
#	boss = Boss(['{}'.format(stock_name[:-4]) for stock_name in os.listdir('/Users/Wiz/Desktop/option/stocks_old') if not '.' in stock_name[:-4]])
#	boss = Boss(['{}'.format(stock_name[:-4]) for stock_name in os.listdir('stocks') if not '.' in stock_name[:-4]])
	#boss = Boss(['AAL'])
	boss = Boss(get_stock_name_list())
	boss.load_config(param.config_path)
	boss.hire_worker()
	boss.assign_task()
	print ('completed!')

def get_stock_name_list():
	from finviz.screener import Screener

	filters = ['exch_nasd']  # Shows companies in NASDAQ which are in the S&P500
	# Get the first 50 results sorted by price ascending
	stock_list = Screener(filters=filters)

	# Export the screener results to .csv
	stock_list.to_csv()

	# Create a SQLite database
	stock_list.to_sqlite()

	stock_name_list = []
	for stock_dict in stock_list.data:
		stock_name_list.append(stock_dict['Ticker'])
	return stock_name_list

#type date contractSymbol strike bid ask bid/strike vol avg_vol |1-(strike/close)| Change 
#MA5 MA20 MA40 MA80 MA40_state MA80_state MA40_state_keep MA80_state_keep situation_type k d

# type：call買權 put賣
# date：2019-10-18
# contractSymbol：ACGL191018C00035000
# strike：履約價
# bid：你要賣出選擇權所得的價格
# ask：你要購買選擇權所需花費的價格，
# bid/strike
# vol：該合約的交易量
# point：如果是SP（牛市）就是supported point，就是顯示出最大價量點x_max，以及 > 0.5x_max的所有價量點
# Interval / topk% / 1-(point/close)：如果是SP（牛市）看現在的close離point多遠，如果為負就是close<point，越負close跌越多，如果為正就是close>point，越正close離支撐點越遠
# change：當天漲幅％
# MA5 MA20 MA40 MA80
# MA40_state MA80_state：1上升、-1下跌
# MA40_state_keep MA80_state_keep：MAXX_state維持了幾個交易日
# situation_type：'big_cow' if MA5 > MA20 > MA40 > MA80 else 'small_cow' if MA40 > MA80 else 'big_bear' if MA5 < MA20 < MA40 < MA80 else 'small_bear'
# k、d

# max_risk：(bp_strike - sp_strike + bid - ask) / sp_strike
# 投報：(bid-ack)/sp_strike

def gui(stock_name):
	# autoclicker
	# https://codereview.stackexchange.com/questions/75710/autoclicker-tkinter-program
	from tkinter import ttk
	from tkinter import Tk, LEFT, BOTH
	import tkinter as tk 
	root = Tk()

	#columns = ('type', 'date', 'contract', 'strike', 'bid', 'ask', 'bid/strike', 'vol', 'point', \
	#	'1-(point/close)', 'max_risk', 'change', 'MA5', 'MA20', 'MA40', 'MA80', 'MA40_state', \
	#	'MA80_state', 'MA40_state_keep', 'MA80_state_keep', 'situation_type', 'k', 'd')

	columns = ('type', 'date', 'contractSymbol', 'strike', 'bid', 'ask', 'bid/strike', 'vol', \
				'interval / topk% / 1-(point/close)', 'change', 'MA5', 'MA20', 'MA40', 'MA80', 'MA40_state(keep)', \
				'MA80_state(keep)', 'situation_type', 'k', 'd')
	treeview = ttk.Treeview(root, height=50, show="headings", columns=columns)  # 表格

	for item in columns:
		if item in ['contractSymbol']:
			width = 200
		elif item in ['interval / topk% / 1-(point/close)']:
			width = 800
		elif item in ['bid/strike']:
			width = 100
		elif item in ['date']:
			width = 110
		elif item in ['bid', 'ask']:
			width = 65
		else:
			width = 50
		treeview.column('{}'.format(item), width=width, anchor='center')
		treeview.heading('{}'.format(item), text='{}'.format(item)) # 显示表头

	treeview.pack(side=LEFT, fill=BOTH)
	#input('wait')
	while True:
		#pass
		#name = ['电脑1','服务器','笔记本']
		#ipcode = ['10.13.71.223','10.25.61.186','10.25.11.163']
		#for i in range(min(len(name),len(ipcode))): # 写入数据
		#	treeview.insert('', i, values=(name[i], ipcode[i]))
		#time.sleep(1)

		def delButton(tree):
			x=tree.get_children()
			for item in x:
				tree.delete(item)
		

		def treeview_sort_column(tv, col, reverse):  # Treeview、列名、排列方式
		    l = [(tv.set(k, col), k) for k in tv.get_children('')]
		    l.sort(reverse=reverse)  # 排序方式
		    # rearrange items in sorted positions
		    for index, (val, k) in enumerate(l):  # 根据排序后索引移动
		        tv.move(k, '', index)
		    tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))  # 重写标题，使之成为再点倒序的标题
		 
		def set_cell_value(event): # 双击进入编辑状态
			for item in treeview.selection():
				#item = I001
				item_text = treeview.item(item, "values")
				#print(item_text[0:2])  # 输出所选行的值
			column= treeview.identify_column(event.x)# 列
			row = treeview.identify_row(event.y)  # 行
			cn = int(str(column).replace('#',''))
			rn = int(str(row).replace('I',''))
			entryedit = Text(root,width=10+(cn-1)*16,height = 1)
			entryedit.place(x=16+(cn-1)*130, y=6+rn*20)
			def saveedit():
				treeview.set(item, column=column, value=entryedit.get(0.0, "end"))
				entryedit.destroy()
				okb.destroy()
			okb = ttk.Button(root, text='OK', width=4, command=saveedit)
			okb.place(x=90+(cn-1)*242,y=2+rn*20)
		 
		#def newrow():
		#	name.append('待命名')
		#	ipcode.append('IP')
		#	treeview.insert('', len(name)-1, values=(name[len(name)-1], ipcode[len(name)-1]))
		#	treeview.update()
		#	newb.place(x=120, y=(len(name)-1)*20+45)
		#	newb.update()
		 
		#treeview.bind('<Double-1>', set_cell_value) # 双击左键进入编辑
		#newb = ttk.Button(root, text='新建联系人', width=20, command=newrow)
		#newb.place(x=120,y=(len(name)-1)*20+45)
		 
		#while True:
		if 1:
			#for col in columns:  # 绑定函数，使表头可排序
			#	treeview.heading(col, text=col, command=lambda _col=col: treeview_sort_column(treeview, _col, False))

	#		input('1')


			period_days = 5
			difference_rate = 0.1
			stock_folder_path = 'stocks'
			option_folder_path = 'options'
			roe_ttm = 1
			t = Trader(period_days, difference_rate, stock_folder_path, option_folder_path, roe_ttm)
			#stock_name = '2330.TW'#'ACGL'

			#stock_name = 'AKAM'#''
			file_path = 'stocks/{}.csv'.format(stock_name)
			options_file_path = 'options/{}.csv'.format(stock_name)
			#print (len(t.crawl_price(stock_name)))
			#data = yf.download("{}".format(stock_name[0:stock_name.find('.')]), start="1960-01-01", end="2019-09-13")
			#data.to_csv(file_path)

			sav_csv_path = '{}.csv'.format(os.path.join(t.stock_folder_path, stock_name))
			df = t.crawl_price(stock_name)

			result_all = t.get_supporting_point(stock_name, file_path)
			t.output_report(stock_name, options_file_path, result_all)
			print ('finish output_report')

			name = ['电脑1','服务器','笔记本']
			ipcode = ['10.13.71.223','10.25.61.186','10.25.11.163']
			#columns = ('type', 'date', 'contract', 'strike', 'bid', 'ask', 'bid/strike', 'vol', 'point', \
			#	'1-(point/close)', 'max_risk', 'change', 'MA5', 'MA20', 'MA40', 'MA80', 'MA40_state', \
			#	'MA80_state', 'MA40_state_keep', 'MA80_state_keep', 'situation_type', 'k', 'd')
			
			df = pd.read_csv(options_file_path)
			delButton(treeview)
			df_shape = df.shape
			for num in range(df_shape[0]):
				row = df[:][num:num+1]
				#print (row['bid'].values)
				if row['bid/strike'].values < t.bid_strike_thre or row['bid'].values == 'nan':
					continue
				insert_value_list = []
				for idx, item in enumerate(columns):
					#input('w1')
					#print (idx, item, row[item].values)
					insert_value_list.append(row[item].values)
					#input('w2')
					#print (idx, type(idx))
					#print (insert_value_list)
				treeview.insert('', num, values=tuple(insert_value_list))#ipcode[i]))
			print ('finish insert')
			count = 0
			root.update()
			#time.sleep(5)
			#while count>pow(100, 100):
			#	count+=1



			
			#root.update()

			

	#		input('3')
		print ('root.mainloop()1')
	root.mainloop()


def gui_old():
	import tkinter
	from tkinter import ttk  # 导入内部包
	import time

	def add_context():
		li = ['王记','{}'.format(time.time()),'男']
		root = tkinter.Tk()
		root.title('测试')
		tree = ttk.Treeview(root,columns=['1','2','3'],show='headings')
		tree.column('1',width=100,anchor='center')
		tree.column('2',width=100,anchor='center')
		tree.column('3',width=100,anchor='center')
		tree.heading('1',text='姓名')
		tree.heading('2',text='学号')
		tree.heading('3',text='性别')
		tree.insert('','end',values=li)
		tree.grid()

	def delButton(tree):
		x=tree.get_children()
		for item in x:
			tree.delete(item)


	while 1:
		li = ['王记','{}'.format(time.time()),'男']

		root = tkinter.Tk()
		root.title('测试')

		tree = ttk.Treeview(root,columns=['1','2','3'],show='headings')
		tree.column('1',width=100,anchor='center')
		tree.column('2',width=100,anchor='center')
		tree.column('3',width=100,anchor='center')
		tree.heading('1',text='姓名')
		tree.heading('2',text='学号')
		tree.heading('3',text='性别')
		tree.insert('','end',values=li)
		tree.grid()
		input('wait')
		delButton(tree)
		del root
	#delButton(tree)
	 
	#root.mainloop()

# ['type', 'date', 'contractSymbol', 'strike', 'bid', \
#				'ask', 'bid/strike', 'vol', 'interval / topk% / 1-(point/close)', \
#				'Change', 'MA5', 'MA20', 'MA40', 'MA80', 'MA40_state(keep)', \
#				'MA80_state(keep)', 'situation_type', 'k', 'd'])
def main_test():
	#gui()
	#assert False
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	roe_ttm = 1
	stock_name = 'APWC'#''
	option_folder_path = 'pickle_result/{}.csv'.format(stock_name)
	# period_days, difference_rate, stock_folder_path, option_folder_path, roe_ttm)
	t = Trader(period_days, difference_rate, stock_folder_path, option_folder_path, roe_ttm)
	#stock_name = '2330.TW'#'ACGL'
	while True:
		
		file_path = 'stocks/{}.csv'.format(stock_name)
		options_file_path = 'options/{}.csv'.format(stock_name)
		#print (len(t.crawl_price(stock_name)))
		#data = yf.download("{}".format(stock_name[0:stock_name.find('.')]), start="1960-01-01", end="2019-09-13")
		#data.to_csv(file_path)

		sav_csv_path = '{}.csv'.format(os.path.join(t.stock_folder_path, stock_name))
		df = t.crawl_price(stock_name)

		result_all = t.get_supporting_point(stock_name, file_path)
		t.output_report(stock_name, options_file_path, result_all)
		gui(stock_name)
		time.sleep(1)

# sp + bp
# type date strike bid ask bid/strike vol |1-(close/strike)| Change MA5 MA20 MA40 MA80 MA40_state MA80_state k d

def main_update_lookuptable(stock_name='ZION'):
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	options_folder_path = 'options'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, options_folder_path, roe_ttm)

	#stock_name = 'ZION'#''
	file_path = 'stocks/{}.csv'.format(stock_name)
	tech_idx_path = 'techidx/{}.csv'.format(stock_name)

	#import time
	#start = time.time()
	m = 20*250
	stock_tech_idx_dict = {}
	stock_tech_idx_dict = t.get_stock_value(file_path, stock_tech_idx_dict, m=m)
	stock_tech_idx_dict = t.get_KD(file_path, stock_tech_idx_dict, nBin=5, nKD=9, m=m)
	stock_tech_idx_dict = t.get_RSI(file_path, stock_tech_idx_dict, nBin=5, n=6, m=m)
	stock_tech_idx_dict = t.get_MA(file_path, stock_tech_idx_dict, Total_day=m-200, percent=1)
	# step 1: 找到n個區段，區段的形成是從某一個股上市到每次歷史交易量新高
	# step 2: 在n個區段中，找到百分比大於50％的支撐點或壓力點，並

	t.output_tech_idx(tech_idx_path, stock_tech_idx_dict)
	#print (time.time()-start)
	#print (stock_tech_idx_dict)

def main_best_contract(stock_name='ZION'):
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	options_folder_path = 'options'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, options_folder_path, roe_ttm)

	stock_name = 'ZION'# ZION AMD
	file_path = 'stocks/{}.csv'.format(stock_name)
	tech_idx_path = 'techidx/{}.csv'.format(stock_name)

	#import time
	#start = time.time()
	m = 20*250
	valid_percentage_sup_pnt_threthod = 0.5
	sup_pnt_close_interval = 100
	valid_percentage_press_pnt_threthod = 0.5
	press_pnt_close_interval = 100

	MACD_short=12
	MACD_long=26
	MACD_signallength=9
	
	stock_tech_idx_dict = {}
	stock_tech_idx_dict = t.get_stock_value(file_path, stock_tech_idx_dict, m=m)
	stock_tech_idx_dict = t.get_KD(file_path, stock_tech_idx_dict, nBin=5, nKD=9, m=m)
	stock_tech_idx_dict = t.get_RSI(file_path, stock_tech_idx_dict, nBin=5, n=6, m=m)
	stock_tech_idx_dict = t.get_MA(file_path, stock_tech_idx_dict, Total_day=m-200, percent=1)

	stock_tech_idx_dict = t.get_MACD(file_path, stock_tech_idx_dict, Total_day_MACD=m, MACD_short=MACD_short, MACD_long=MACD_long, MACD_signallength=MACD_signallength)

	stock_tech_idx_dict = t.get_supported_point(file_path, stock_tech_idx_dict, sup_pnt_close_interval=sup_pnt_close_interval, valid_percentage_sup_pnt_threthod=valid_percentage_sup_pnt_threthod)
	stock_tech_idx_dict = t.get_pressed_point(file_path, stock_tech_idx_dict, press_pnt_close_interval=press_pnt_close_interval, valid_percentage_press_pnt_threthod=valid_percentage_press_pnt_threthod)

	t.output_tech_idx(tech_idx_path, stock_tech_idx_dict)
	#print (time.time()-start)
	#print (stock_tech_idx_dict)

def main_back_testing():
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	options_folder_path = 'options'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, options_folder_path, roe_ttm)

	stock_name = 'ZION'# ZION AMD
	options_contract_file_path = 'options/{}.csv'.format(stock_name)
	tech_idx_path = 'techidx/{}.csv'.format(stock_name)
	file_path = 'stocks/{}.csv'.format(stock_name)
	result_all = t.get_supporting_point(stock_name, file_path)

	sav_stock_csv_path = '{}.csv'.format(os.path.join(t.stock_folder_path, stock_name))
	options_file_path = '{}.csv'.format(os.path.join(t.option_folder_path, stock_name))
	options_com_order_csv_path = '{}.csv'.format(os.path.join(t.option_com_order_folder_path, stock_name))

	df = t.crawl_price(stock_name)
	combin_contract_list_all = t.output_report(stock_name, options_file_path, options_com_order_csv_path, result_all)
	best_combin_contract_all = t.back_testing(tech_idx_path, options_contract_file_path, combin_contract_list_all)
	print (best_combin_contract_all)
	'''
	Close = 47.95
	MA = 1
	MACD = 4
	D = 3
	RSI = 4
	Supported_point = {'25.52': 1.0, '9.68': 0.76, '18.48': 0.65}
	Pressed_point = {'17.6': 1.0, '14.08', 0.95, '28.16': 0.51}
	tech_idx_dict_today = {'Close': Close, 'MA': MA, 'MACD': MACD, 'D': D, 'RSI': RSI, \
							'Supported_point': Supported_point, 'Pressed_point': Pressed_point, \
							'strike_date': '2019-12-20', 'strike_price': 39.0 }
	probability = t.back_testing_byDTree(tech_idx_path, tech_idx_dict_today)
	print (probability)
	'''
def sorted_by_prob(final_csv_list_all, sorted_item):
	#print (final_csv_list_all)
	final_csv_list_all_sorted = []
	for final_csv_dict in final_csv_list_all:
		under_idx = 0
		for final_csv_dict_sorted in final_csv_list_all_sorted:
			if final_csv_dict_sorted[sorted_item] > final_csv_dict[sorted_item]:
				under_idx+=1
		final_csv_list_all_sorted.insert(under_idx, final_csv_dict)
	print (final_csv_list_all_sorted)
	#input('wait')
	return final_csv_list_all_sorted

def main_combine_csv():
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	options_folder_path = 'options'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, options_folder_path, roe_ttm)

	final_csv_list_all = []
	for final_csv in glob.glob('{}/*.csv'.format(t.option_com_order_folder_path)):
		with open(final_csv, 'r') as f_r:
			final_csv_list = json.loads(f_r.readlines()[0])
			final_csv_list_all.extend(final_csv_list)
			#print (final_csv_list_all)

	#final_csv_list_all = sorted_by_prob(final_csv_list_all, 'un_hit_probability')

	with open(os.path.join(t.option_com_order_folder_path, 'ALL.csv'), 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		#item_list = ['sell_contractSymbol', 'buy_contractSymbol', 'except_value', 'sample_num', 'close', 'un_hit_probability', 'return_on_invest', 'date']
		item_list = ['type', 'stock', 'sell_strike', 'buy_strike', 'except_value', 'sample_num', 'close', 'un_hit_probability', 'return_on_invest', 'date']
		writer.writerow(item_list)
		for final_csv_dict in final_csv_list_all:
			content_list = []
			for item in item_list:
				if item in ['type', 'stock', 'sell_strike', 'buy_strike']:
					date = final_csv_dict['date'].split('-')[0][2:] + final_csv_dict['date'].split('-')[1] + final_csv_dict['date'].split('-')[2]
					stock = final_csv_dict['sell_contractSymbol'][:final_csv_dict['sell_contractSymbol'].find(date)]
					typ_s = final_csv_dict['sell_contractSymbol'][final_csv_dict['sell_contractSymbol'].find(date)+len(date):final_csv_dict['sell_contractSymbol'].find(date)+len(date)+1]
					typ = 'PCS' if typ_s == 'P' else 'CCS'
					sell_strike = int(final_csv_dict['sell_contractSymbol'][-7:len(final_csv_dict['buy_contractSymbol'])]) / 1000
					buy_strike = int(final_csv_dict['buy_contractSymbol'][-7:len(final_csv_dict['buy_contractSymbol'])]) / 1000
					content_list.append(typ)
					content_list.append(stock)
					content_list.append(sell_strike)
					content_list.append(buy_strike)
				else:
					try:
						content_list.append(round(float(final_csv_dict[item]), t.interval_value_point))
					except:
						content_list.append(final_csv_dict[item])
			writer.writerow(content_list)

if __name__ == '__main__':
	main()
	#main_combine_csv()
	#main_update_lookuptable()
	#main_best_contract()
	#main_test()
	#main_back_testing()
