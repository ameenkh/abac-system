
import multiprocessing

bind = "0.0.0.0:9876"
worker_class = "aiohttp.GunicornUVLoopWebWorker"
workers = multiprocessing.cpu_count() * 2 + 1
access_log_format = "%P %a %t %r %s %Tf"
