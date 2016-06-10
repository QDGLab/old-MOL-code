"""
"""

__all__ = ["emit","connect"]
__observers = {}

def emit(signal_name,*args,**kw):
#    print "emit: ",signal_name
    for o in __observers.get(signal_name,[]):
        o(*args,**kw)

def connect(signal_name,observer):
    if not signal_name in __observers:
        __observers[signal_name] = []
    
    __observers[signal_name].append(observer)

