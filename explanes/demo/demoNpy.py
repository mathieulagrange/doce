import explanes as exp
from time import sleep
from pandas import DataFrame
import time
import numpy as np
from pathlib import Path

# use case where:
#   - the results are stored on disk using npy files
#   - one factor affects the size of the results vectors
#   - the metrics does not operate on the same data, resulting on result vectors with different sizes per metric

def set(experiment, args):
  experiment.project.name = 'demoNpy'
  experiment.project.description = 'demonstration of npy storage of metrics'
  experiment.project.author = 'mathieu Lagrange'
  experiment.project.address = 'mathieu.lagrange@ls2n.fr'
  experiment.project.version = '0.1'

  experiment.path.output = '/tmp/'+experiment.project.name+'/'
  experiment.path.code = '~/tools/explanes.py/'
  experiment.makePaths()

  experiment._idFormat = {'format': 'hash'}

  experiment.host = ['pc-lagrange.irccyn.ec-nantes.fr']

  experiment.factor.dataType = ['float', 'double']
  experiment.factor.datasetSize = 1000*np.array([1, 2, 4, 8])
  experiment.factor.meanOffset = 10**np.array([0, 1, 2, 3])
  experiment.factor.nbRuns = [2000, 4000]

  experiment.metric.mae = ['mean-0', 'std-0']
  experiment.metric.mse = ['mean-1%', 'std-1']
  experiment.metric.duration = ['mean']
  return experiment

def step(setting, experiment):
  settingMae = np.zeros((setting.nbRuns))
  settingMse = np.zeros((setting.nbRuns))

  # print(settingMse.shape)
  tic = time.time()
  for r in range(setting.nbRuns):
    data = np.zeros((2, setting.datasetSize), dtype=np.float32)
    offset = setting.meanOffset*np.random.rand(1)
    data[0, :] = 1.0+offset
    data[1, :] = 0.1-offset

    reference = ((data[0, 0]-0.55)**2 + (data[1, 0]-0.55)**2)/2

    if setting.dataType is 'float':
        estimate = np.var(data)
    elif setting.dataType is 'double':
        estimate =  np.var(data, dtype=np.float64)
    settingMse[r] = abs(reference - estimate)
    settingMae[r] = np.square(reference - estimate)

  baseFileName = setting.getId(**experiment._idFormat)
  np.save(experiment.path.output+baseFileName+'_mae.npy', settingMae)
  np.save(experiment.path.output+baseFileName+'_mse.npy', settingMse)
  duration = time.time()-tic
  np.save(experiment.path.output+baseFileName+'_duration.npy', duration)

# uncomment this to fine tune display of metrics
# def display(experiment, settings):
#     (data, desc, header)  = experiment.metric.get('mae', settings, experiment.path.output, **experiment._idFormat)
#
#     print(header)
#     print(desc)
#     print(len(data))
