import doce
from time import sleep
from pandas import DataFrame
import time
import numpy as np
from pathlib import Path

if __name__ == "__main__":
  doce.run.run()

# use case where:
#   - the results are stored on disk using npy files
#   - one factor affects the size of the results vectors
#   - the metrics does not operate on the same data, resulting on result vectors with different sizes per metric

def set(userData):
  experiment = doce.Experiment(
    name = 'npyDemo',
    purpose = 'demonstration of npy storage of metrics',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
    version = '0.1',
    host = ['pc-lagrange.irccyn.ec-nantes.fr']
  )

  experiment.setPath('output', '/tmp/'+experiment.name+'/')

  experiment.addPlan('plan',
    dataType= ['float', 'double'],
    datasetSize = 1000*np.array([1, 2, 4, 8], dtype=np.intc),
    meanOffset = 10.0**np.array([0, 1, 2]),
    nbRuns = 2000
    )

  experiment.setMetrics(
    mae = ['sqrt|mean-0*-', 'std%-'],
    mse = ['mean*', 'std%'],
    duration = ['mean']
  )

  experiment._display.metricPrecision = 10
  experiment._display.bar = False

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

    if setting.dataType == 'float':
        estimate = np.var(data)
    elif setting.dataType == 'double':
        estimate =  np.var(data, dtype=np.float64)

    settingMse[r] = abs(reference - estimate)
    settingMae[r] = np.square(reference - estimate)

  if setting.dataType == 'float':
    np.save(experiment.path.output+setting.id()+'_mae.npy', settingMae)
  np.save(experiment.path.output+setting.id()+'_mse.npy', settingMse)
  duration = time.time()-tic
  # np.save(experiment.path.output+setting.id()+'_duration.npy', duration)

# uncomment this method to fine tune display of metrics
def myDisplay(experiment, settings):
  (data, desc, header)  = experiment.metric.get('mae', settings, experiment.path.output, settingEncoding = experiment._settingEncoding)

  print(header)
  print(desc)
  print(len(data))
