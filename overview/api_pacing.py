"""Serialize model bursts and learn the interval from explicit RPM violations."""
import threading
import time

LOCK=threading.Lock()
BUCKETS={}


def wait(model,callback=None):
    if not model:return
    with LOCK:
        bucket=BUCKETS.setdefault(model,{'next':0.,'interval':1.})
        now=time.monotonic();delay=max(0,bucket['next']-now)
        bucket['next']=max(now,bucket['next'])+bucket['interval']
    if delay:
        if callback:callback(delay)
        time.sleep(delay)


def defer(model,delay,limits=()):
    if not model:return
    with LOCK:
        bucket=BUCKETS.setdefault(model,{'next':0.,'interval':1.})
        for limit in limits:
            if limit['tipo']=='RPM' and limit.get('valor') and limit['valor']>0:
                bucket['interval']=max(bucket['interval'],60/limit['valor']+.1)
        bucket['next']=max(bucket['next'],time.monotonic()+delay)
