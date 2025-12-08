"""
InstanceTracker - A metaclass for tracking object instances with weakref and context managers
"""
from instance_tracker import InstanceCounter
print(InstanceCounter.get_global_stats())