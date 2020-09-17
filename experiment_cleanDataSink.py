import explanes as el
import numpy as np
import os

e=el.experiment.Experiment()
e.path.output = '/tmp/test'
e.makePaths(force=True)

e.factor.factor1=[1, 3]
e.factor.factor2=[2, 4]

def myFunction(setting, experiment):
  np.save(experiment.path.output+'/'+setting.getId()+'_sum.npy', e.factor.factor1+e.factor.factor2)
  np.save(experiment.path.output+'/'+setting.getId()+'_mult.npy', e.factor.factor1*e.factor.factor2)

e.do([], myFunction, tqdmDisplay=False)
print(os.listdir(e.path.output))

e.cleanDataSink('output', [0], force=True)
print(os.listdir(e.path.output))

e.cleanDataSink('output', [1, 1], force=True, reverse=True, selector='*mult*')
print(os.listdir(e.path.output))
