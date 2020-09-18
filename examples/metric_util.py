import explanes as el
import numpy as np
m = el.metric.Metric()
m.duration = ['mean']
m._unit.duration = 'seconds'
m._description.duration = 'duration of the trial'
m.mse = ['mean']
m._unit.mse = ''
m._description.mse = 'Mean Square Error'
print(len(m))
print(m.getMetricNames())
print(m)
