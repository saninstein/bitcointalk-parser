from datetime import datetime


def chrome_headers(referer=None):
	return {
		'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
		'referer': referer,
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
	}


def str_to_seconds(t):
	utc_dt = datetime.strptime(t, '%B %d, %Y, %I:%M:%S %p')
	return (utc_dt - datetime(1970, 1, 1)).total_seconds()


def today_part():
	return datetime.utcnow().strftime("%B %d, %Y,")
