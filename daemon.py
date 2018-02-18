import time
from datetime import datetime
from workers.bitcointalk_worker import BitcointalkDataWorker


workers = [
    BitcointalkDataWorker(),
]

for p in workers:
    p.run()

while True:
    for p in workers:
        p.ping()

    time.sleep(10)
