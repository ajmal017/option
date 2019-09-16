# http://www.liujiangblog.com/course/python/82
# 20190902 future work
# analysis_statement當做基本面filter
# 將通過analysis_statement當做基本面filter的股票下載yahoo finance的.csv
# 再算get_supporting_point
# 繼續把皓謙講的做完

# https://github.com/dsmbgu8/image_annotate.py/issues/4
# echo "backend: TkAgg" >> ~/.matplotlib/matplotlibrc

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
import fix_yahoo_finance as yf
import datetime

import finviz
import copy
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
# stock_dict = {	supported_point: {  Interval: xxx 
#										vol_val: xxx	},
#					topk_vol:		[{'volume': max_volume, 'close': max_volume_close}, 
#									{'volume': max_volume2, 'close': max_volume_close2}....],
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
	def __init__(self, period_days, difference_rate, stock_folder_path, roe_ttm):
		self.stock_name = -1
		self.period_days = period_days
		self.difference_rate = 0.05#difference_rate
		self.roe_ttm = roe_ttm
		self.stock_folder_path = stock_folder_path
		self.value_group = -1
		self.top_volume_num = 10
		self.part_num = 100

#

	def get_supporting_point(self, stock_name, file_path):
		stock_dict_sum = {'supported_point':{},'topk_vol':[],'moving_average':{}}
		stock_dict = {}
		stock_close_list = []
		press_list = []
		stock_date_list = []
		stock_volume_list = []
		count = 0
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				count+=1
				#if count < 12085 or count > 12095:#or count > 13500:
				#	continue
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date,Open,High,Low,Close,Adj_Close,Volume = line[0], line[1], line[2], line[3], line[4], line[5], int(line[6].strip('\n'))
				stock_dict[Date] = {'Date': Date,
									'Open': Open,
									'High': High,
									'Low': Low,
									'Close': Close,
									'Adj_Close': Adj_Close,
									'Volume': Volume}
				stock_close_list.append(float(Close))
				stock_volume_list.append(int(Volume))
				stock_date_list.append(Date)
		#print (stock_dict)
		#print (stock_name, 'get_supporting_point')

		# top3 volume
		top3_volume_list = []
		stock_volume_list_tmp = copy.deepcopy(stock_volume_list)
		for num in range(self.top_volume_num):
			max_volume = max(stock_volume_list_tmp)
			stock_volume_list_tmp.remove(max_volume)
			max_idx = stock_volume_list.index(max_volume)
			max_date = stock_date_list[max_idx]
			max_volume_close = stock_close_list[max_idx]
			top3_volume_list.append({max_date: {'volume': max_volume, \
												'close': max_volume_close}})
		print (top3_volume_list)

		"""
		# press
		for idx, Close in enumerate(stock_close_list):
			if idx < self.period_days or idx+self.period_days > len(stock_close_list):
				continue
			Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
			if not Close > Close_five_days_pass_min*1.1:
				continue
			Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
			if not Close > Close_five_days_pass_max:
				continue
			Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
			if not Close > Close_five_days_next_max:
				continue
			Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
			if not Close > Close_five_days_next_min*1.1:
				continue
			#print (idx, Close)
			press_dict = {'Date': stock_date_list[idx],
							'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
							'Close': Close}
			press_list.append(press_dict)
		print (press_list)
		"""

		support_list = []
		# support
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
			support_dict = {'Date': stock_date_list[idx],
							'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
							'Close': Close}
			support_list.append(support_dict)
		#print (support_list)

		support_all_dict = {}
		part_value = round(max(stock_close_list) / self.part_num, 3)
		for num in range(self.part_num):
			support_all_dict['{}_{}'.format(round(part_value*num, 3), round(part_value*(num+1), 2))] = 0
		for support_dict_tmp in support_list:
			num = int(support_dict_tmp['Close'] / part_value)
			support_all_dict['{}_{}'.format(round(part_value*num, 3), round(part_value*(num+1), 2))] \
				+=support_dict['Volume_Value']

		#print (support_all_dict)
		support_all_list = []
		for key in support_all_dict.keys():
			if support_all_dict[key] == 0:
				continue
			if support_all_list == []:
				support_all_list.append({'Interval': key, \
										'Volume_Value': support_all_dict[key]})
			else:
				insert_idx = 0
				for support_dict in support_all_list:
					#print (support_dict)
					#print (support_dict['Volume_Value'], support_all_dict[key])
					if support_dict['Volume_Value'] >= support_all_dict[key]:
						insert_idx += 1
					else:
						break
				support_all_list.insert(insert_idx, {'Interval': key, \
										'Volume_Value': support_all_dict[key]})
		print (support_all_list)

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
		if not stock_dict['Optionable'] == 'Yes':
			return False
		if not 'M' in stock_dict['Avg Volume']:
			return False
		if '-' in stock_dict['ROE']:
			return False
		if float(stock_dict['ROE'][:-1]) < 10.0:
			return False
		if float(stock_dict['EPS (ttm)']) > 0.0:
			return False

		return True
		#if 'K' stock_dict['Avg Volume'] or :

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
			stock_name = stock_queues.get()
			if self.analysis_statement(stock_name):
				continue

			sav_csv_path = '{}.csv'.format(os.path.join(self.stock_folder_path, stock_name))
			data = yf.download("{}".format(stock_name[0:stock_name.find('.')]), start="1960-01-01", end="2020-12-31")
			data.to_csv(sav_csv_path)
			self.get_supporting_point(stock_name, sav_csv_path)
			print ('worker number {}, stock_name is {}'.format(workers_num, stock_name))
			#time.sleep(1)


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
			trader = copy.deepcopy(Trader(self.period_days, self.difference_rate, self.stock_folder_path, self.roe_ttm))
			print ('worker {}'.format(i))
			self.workers.append(trader)

	def assign_task(self):
		for i in range(self.num_worker):
			p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			p.start()
			p.join(timeout=0.1)

			#p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			#p.start()
			#p.join(timeout=0.1)

		print ('assign task finish!')


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--config_path', type=str)
	return parser.parse_args()

def main():
	param = get_args()
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

def main_temp():
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, roe_ttm)
	stock_name = 'AAL'
	file_path = '/Users/Wiz/Desktop/option/stocks/AAL.csv'
	t.get_supporting_point(stock_name, file_path)

if __name__ == '__main__':
	main_temp()