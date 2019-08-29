# http://www.liujiangblog.com/course/python/82

import copy
import argparse
import multiprocessing
from multiprocessing import Process
from multiprocessing import queues
import time

import os

class Trader(object):
	def __init__(self):
		self.stock_name = -1
		self.period_days = -1
		self.difference_rate = -1

	def analysis_document(self, workers_num, stock_queues):
		"""
		calculating the supporting point and stress point
		"""
		while not stock_queues.empty():
			stock_name = stock_queues.get()
			print ('worker number {}, stock_name is {}'.format(workers_num, stock_name))
			time.sleep(1)


class Boss(object):
	def __init__(self):
		self.stock_queues = queues.Queue(20, ctx=multiprocessing)
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

		config_lines = open(config_path,'r').readlines()
		for stock_name in os.listdir(config_lines[0].strip()):
			self.stock_queues.put(stock_name)

		self.num_worker = int(config_lines[1].strip())
		#self.period_days = int(config_lines[2].strip())
		#self.difference_rate = float(config_lines[3].strip())


	def hire_worker(self):
		"""
		using multiprocess to process .csv, we will enable self.num_worker thread to process data
		"""
		for i in range(self.num_worker):
			trader = copy.deepcopy(Trader())
			self.workers.append(trader)

	def assign_task(self):
		for i in range(self.num_worker):
			p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			p.start()
			p.join(timeout=0.1)
		print ('assign task finish!')


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--config_path', type=str)
	return parser.parse_args()

def main():
	param = get_args()
	boss = Boss()
	boss.load_config(param.config_path)
	boss.hire_worker()
	boss.assign_task()
	print ('completed!')


if __name__ == '__main__':
	main()