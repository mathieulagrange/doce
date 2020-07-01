import explanes as exp
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
  config = exp.Config()
  config.project.name = 'demoNpy'
  config.project.description = 'demonstration of npy storage of metrics'
  config.project.author = 'mathieu Lagrange'
  config.project.address = 'mathieu.lagrange@ls2n.fr'
  config.project.version = '0.1'

  config.path.output = '/tmp/'+config.project.name+'/'
  config.makePaths()

  config.factor.dataType = ['float', 'double']
  config.factor.datasetSize = 1000*np.array([1, 2, 4, 8])
  config.factor.meanOffset = 10**np.array([0, 1, 2, 3, 4])
  config.factor.nbRuns = [20, 40]

  config.metric.mae = ['mean-0%', 'std-0']
  config.metric.mse = ['mean-1', 'std-1']
  config.metric.duration = ['mean%']
  #config.metric.units.duration = 'seconds'

  print(config)

  compute = True
  if compute:
    print('computing...')
    config.do([], step, logFileName=config.path.output+'log.txt') #
    print('done')
  # reduce from npy data
  print('Results:')
  (table, columns, header) = config.metric.reduce(config.factor.settings([-1, -1, -1, 0]), config.path.output, naming='hash')
  print(header)
  df = DataFrame(table, columns=columns)
  print(df)
  # get from npy data
  (data, legend, title) = config.metric.get('mae', config.factor.settings([0, -1, -1, 0]), config.path.output, naming='hash')
  print('The legend of the figure :')
  print(legend)
  print('The title of the figure: '+title)

def step(setting, config):
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

  np.save(config.path.output+setting.getId('hash')+'_mae.npy', settingMae)
  np.save(config.path.output+setting.getId('hash')+'_mse.npy', settingMse)
  duration = time.time()-tic
  np.save(config.path.output+setting.getId('hash')+'_duration.npy', duration)

if __name__ == '__main__':
  main()
