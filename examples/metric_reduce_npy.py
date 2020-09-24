import explanes as el
import numpy as np
import pandas as pd

experiment = el.experiment.Experiment()
experiment.project.name = 'example'
experiment.path.output = '/tmp/'+experiment.project.name+'/'
experiment.factor.f1 = [1, 2]
experiment.factor.f2 = [1, 2, 3]
experiment.metric.m1 = ['mean', 'std']
experiment.metric.m2 = ['min', 'argmin']

def process(setting, experiment):
  metric1 = setting.f1+setting.f2+np.random.randn(100)
  metric2 = setting.f1*setting.f2*np.random.randn(100)
  np.save(experiment.path.output+setting.getId()+'_m1.npy', metric1)
  np.save(experiment.path.output+setting.getId()+'_m2.npy', metric2)

experiment.makePaths()
experiment.do([], process, progress=False)

(table, columns, header) = experiment.metric.reduce(experiment.factor.settings(), experiment.path.output)

df = pd.DataFrame(table, columns=columns).round(decimals=2)
print(df)
