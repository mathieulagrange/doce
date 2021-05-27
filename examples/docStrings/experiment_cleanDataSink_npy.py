import explanes as el
import numpy as np
import os
e=el.experiment.Experiment()
e.path.output = '/tmp/test'
e.setPath()
e.factor.factor1=[1, 3]
e.factor.factor2=[2, 4]
def myFunction(setting, experiment):
  np.save(experiment.path.output+'/'+setting.id()+'_sum.npy', setting.factor1+setting.factor2)
  np.save(experiment.path.output+'/'+setting.id()+'_mult.npy', setting.factor1*setting.factor2)
nbFailed = e.do([], myFunction, progress=False)
os.listdir(e.path.output)
['factor1_3_factor2_2_sum.npy', 'factor1_3_factor2_2_mult.npy', 'factor1_3_factor2_4_mult.npy', 'factor1_1_factor2_2_sum.npy', 'factor1_1_factor2_4_mult.npy', 'factor1_3_factor2_4_sum.npy', 'factor1_1_factor2_2_mult.npy', 'factor1_1_factor2_4_sum.npy']

e.cleanDataSink('output', [0], force=True)
os.listdir(e.path.output)
['factor1_3_factor2_2_sum.npy', 'factor1_3_factor2_2_mult.npy', 'factor1_3_factor2_4_mult.npy', 'factor1_3_factor2_4_sum.npy']

e.cleanDataSink('output', [1, 1], force=True, reverse=True, selector='*mult*')
os.listdir(e.path.output)
['factor1_3_factor2_2_sum.npy', 'factor1_3_factor2_4_mult.npy', 'factor1_3_factor2_4_sum.npy']
