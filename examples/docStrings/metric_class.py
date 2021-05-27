import explanes as el
m = el.metric.Metric()
m.duration = ['mean', 'std']
m._unit.duration = 'second'
m._description = 'duration of the processing'

m.metric1 = ['median-0', 'min-0', 'max-0']

m.metric2 = ['median-2', 'min-2', 'max-2', '0']
