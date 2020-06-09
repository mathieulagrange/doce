from explanes import Factors, Metrics
from tqdm import trange
from time import sleep
from pandas import DataFrame
import time
import os
import numpy as np


# more complex case where:
#   - the results are stored on disk using npy files
#   - one factor affects the size of the results vectors
#   - the metrics does not operate on the same data, resulting on result vectors with different sizes per metric

def main():
  resultPath = '/tmp/results/'
  if not os.path.exists(resultPath):
      os.makedirs(resultPath)

  factors = Factors()

  factors.dataType = ['float', 'double']
  factors.datasetSize = 1000*np.array([1, 2, 4, 8])
  factors.meanOffset = 10**np.array([0, 1, 2, 3, 4])
  factors.nbRuns = [20, 40]

  metrics = Metrics()

  metrics.mae = ['mean', 'std']
  metrics.mse = ['mean', 'std']
  metrics.duration = ['']
  #metrics.units.duration = 'seconds'

  compute = True
  if compute:
    print('computing...')
    factors.settings().do(step, resultPath, logFileName=resultPath+'log.txt')
    print('done')
  # reduce from npy data
  print('Results:')
  (table, columns, header) = metrics.reduce(factors.settings([-1, -1, -1, 0]), resultPath, naming='hash')
  # print(columns)
  print(header)
  df = DataFrame(table, columns=columns)
  print(df)

def step(setting, resultPath):
  tre
  settingMae = np.zeros((setting.nbRuns))
  settingMse = np.zeros((setting.nbRuns))

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

  np.save(resultPath+setting.getId('hash')+'_mae.npy', settingMae)
  np.save(resultPath+setting.getId('hash')+'_mse.npy', settingMse)
  duration = time.time()-tic
  np.save(resultPath+setting.getId('hash')+'_duration.npy', duration)

if __name__ == '__main__':
  main()
