# http://www.liujiangblog.com/course/python/82
# 20190902 future work
# analysis_statement當做基本面filter
# 將通過analysis_statement當做基本面filter的股票下載yahoo finance的.csv
# 再算get_supporting_point
# 繼續把皓謙講的做完

import copy
import argparse
import multiprocessing
from multiprocessing import Process
from multiprocessing import queues
import time

import pickle

import os

import finviz
#print (finviz.get_stock('STX'))
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


class Trader(object):
	def __init__(self, period_days, difference_rate, stock_folder_path):
		self.stock_name = -1
		self.period_days = period_days
		self.difference_rate = difference_rate
		self.stock_folder_path = stock_folder_path

	def get_supporting_point(self, stock_name, file_path):
		stock_dict = {}
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date,Open,High,Low,Close,Adj_Close,Volume = line[0], line[1], line[2], line[3], line[4], line[5], line[6]
				stock_dict[Date] = {'Open': Open,
									'High': High,
									'Low': Low,
									'Close': Close,
									'Adj_Close': Adj_Close,
									'Volume': Volume}
		#print (stock_dict)
		print (stock_name, 'get_supporting_point')

	def analysis_statement(self, stock_name):
		stock_dict = finviz.get_stock(stock_name)
		if not stock_dict['Optionable'] == 'Yes':
			return False

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
			stock_name = 'AMD.csv'
			#if self.analysis_statement(stock_name):
			#	continue
			file_path = os.path.join(self.stock_folder_path, stock_name)
			self.get_supporting_point(stock_name, file_path)
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
			self.num_worker = int(config_lines[2].strip())
			self.period_days = int(config_lines[3].strip())
			self.difference_rate = float(config_lines[4].strip())

	def hire_worker(self):
		"""
		using multiprocess to process .csv, we will enable self.num_worker thread to process data
		"""
		for i in range(self.num_worker):
			trader = copy.deepcopy(Trader(self.period_days, self.difference_rate, self.stock_folder_path))
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

if __name__ == '__main__':
	main()