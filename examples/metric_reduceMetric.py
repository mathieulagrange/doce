import explanes as el
import numpy as np

data = np.linspace(1, 10, num=10)
print(data)
m  =el.metric.Metric()
print(m.reduceMetric(data, 0))
print(m.reduceMetric(data, 8))
print(m.reduceMetric(data, 'sum%'))
print(m.reduceMetric(data, 'sum-0'))
print(m.reduceMetric(data, 'sum-1'))
print(m.reduceMetric(data, 'sum-2'))
