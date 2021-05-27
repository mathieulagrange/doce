import doce
from time import sleep
from pandas import DataFrame
import time
import numpy as np
from pathlib import Path
import os

if __name__ == "__main__":
  doce.run.run()


def set(args):
  experiment = doce.Experiment(
    name = os.path.basename(__file__)[:-3]
    )

  experiment.setPath('output', '/tmp/'+experiment.name+'/')

  experiment.addPlan('xp1',
    method = ['methodOne'],
    parameterMethodOne = ['modalityOne', 'modalityTwo']
  )

  experiment.addPlan('xp2',
    method = ['methodTwo'],
    parameterMethodTwo = [1, 2, 3]
  )

  experiment.setMetrics(m = ['mean'])

  return experiment

def step(setting, experiment):
  print(setting.id())
  np.save(experiment.path.output+setting.id()+'_m.npy', 0)
