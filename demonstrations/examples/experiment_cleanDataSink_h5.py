import explanes as el
import tables as tb

e=el.experiment.Experiment()
e.path.output = '/tmp/test.h5'

e.factor.factor1=[1, 3]
e.factor.factor2=[2, 4]

e.metric.sum = ['']
e.metric.mult = ['']

def myFunction(setting, experiment):
  h5 = tb.open_file(experiment.path.output, mode='a')
  sg = experiment.metric.addSettingGroup(h5, setting, metricDimension={'sum':1, 'mult':1})
  sg.sum[0] = setting.factor1+setting.factor2
  sg.mult[0] = setting.factor1*setting.factor2
  h5.close()

nbFailed = e.do([], myFunction, progress=False)
h5 = tb.open_file(e.path.output, mode='r')
print(h5)
h5.close()

e.cleanDataSink('output', [0], force=True)
h5 = tb.open_file(e.path.output, mode='r')
print(h5)
h5.close()

e.cleanDataSink('output', [1, 1], force=True, reverse=True, selector='*mult*')
h5 = tb.open_file(e.path.output, mode='r')
print(h5)
h5.close()
