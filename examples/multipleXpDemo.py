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

  experiment.xp1 = doce.Plan(
    method = ['methodOne'],
    parameterMethodOne = ['modalityOne', 'modalityTwo']
  )
  experiment.xp2 = doce.Plan(
    method = ['methodTwo'],
    parameterMethodTwo = [1, 2, 3]
  )

  # experiment.factor.truc = doce.factor.Factor() #['machin', 'bidule']

  experiment.metric = doce.Metric(m = ['mean'])

  return experiment

def step(setting, experiment):
  print(setting.id())
  np.save(experiment.path.output+setting.id()+'_m.npy', 0)
