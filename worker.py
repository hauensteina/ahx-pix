"""
worker.py
Andreas Hauenstein
Created: Jan 2023

Register a worker for background jobs on Redis Queue
"""

from pdb import set_trace as BP
import os
import redis
from rq import Worker, Queue, Connection
from mod_ahx_pics import REDIS_CONN

if __name__ == '__main__':
    with Connection( REDIS_CONN):
        worker = Worker( Queue('myq'))
        worker.work()