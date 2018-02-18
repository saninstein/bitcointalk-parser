import aiohttp
from aiohttp.web_exceptions import HTTPNotFound
import asyncio
import re
import logging as log
from . import helpers
from lib.data_worker import DataWorker


log.basicConfig(format = u'%(filename)s[LINE:%(lineno)d] %(levelname)-8s [%(asctime)s] %(message)s', level = log.INFO)

BASE_URL = 'https://bitcointalk.org/index.php?topic={}.1000000000'

PROJECTS_URL = 'http://db.xyz.hcmc.io/data/coins.json'

ITEM_PATTERN = re.compile(r'bitcointalk.org/index.php\?topic=(\d+).?')
NUM_POST_PATTERN = re.compile(r'ignmsgbttns(\d+)\"')
TIME_PATTERN = re.compile(r'smalltext\"\>([A-z]+ \d\d, \d\d\d\d, \d\d:\d\d:\d\d \w\w)|(<b>Today</b> at \d\d:\d\d:\d\d \w\w)')
ERROR_MESSAGE = "The topic or board you are looking for appears to be either missing or off limits to you."

class BitcointalkDataWorker(DataWorker):

	update_frequency = 60 * 10

	def __init__(self, loop=asyncio.get_event_loop()):
		self.loop = loop
		self.session = None
		self.semaphore = asyncio.Semaphore(5)
		self.headers = helpers.chrome_headers("google.com")

	def fetch_data(self):
		self.loop.run_until_complete(self._fetch_data())

	def save(self, coin_id, data):
		if data is None:
			return
		print(coin_id, data)

	async def _fetch_data(self):
		projects = await self.fetch(PROJECTS_URL, json=True)
		for project in projects:
			if not ('community' in project and 'bitcointalk' in project['community']):
				continue

			info = dict(posts=0, last_post=-1, errors=[])
			urls = project['community']['bitcointalk']
			for url in urls:
				item = ITEM_PATTERN.findall(url)
				if not item:
					info['errors'].append('No items')
					continue
				item = item[0]

				# aggregate data
				try:
					item_info = await self.get_info(item)
					info['posts'] += item_info['posts']
					info['last_post'] = max([info['last_post'], item_info['last_post']])
					if 'error' in item_info:
						info['errors'].append(item_info['error'])
				except HTTPNotFound:
					info['errors'].append((url, 'Not Found'))

			info['last_post'] = info['last_post'] if info['last_post'] != -1 else None

			if not info['errors']:
				info.pop('errors', None)

			self.save(project['id'], info)

	async def get_info(self, item):
		res = await self.fetch(BASE_URL.format(item))

		if ERROR_MESSAGE in res:
			return {
				'posts': 0,
				'last_post': -1,
				'error': (item, "Not Found")
			}

		num_posts = NUM_POST_PATTERN.findall(res)[-1]
		time_str = TIME_PATTERN.findall(res)[-1]
		if time_str[1]:
			# replace Today string -> Month and day part
			today_part = helpers.today_part()
			time_str = time_str[1].replace("<b>Today</b> at", today_part)
		else:
			time_str = time_str[0]

		ts = helpers.str_to_seconds(time_str)
		
		return {
			'posts': int(num_posts),
			'last_post': int(ts)
		}

	async def close_session(self):
		if self.session:
			await self.session.close()
			self.session = None

	async def fetch(self, url, json=False):
		if self.session is None:
			self.session = aiohttp.ClientSession(headers=self.headers)

		if not json:
			await asyncio.sleep(0.5)
		async with self.semaphore:
			async with self.session.get(url) as res:
				log.debug(f"{url} [{res.status}]")
				if res.status == 404:
					raise HTTPNotFound
				if json:
					return await res.json()
				return await res.text()
