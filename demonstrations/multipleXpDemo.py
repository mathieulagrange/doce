import explanes as el
from time import sleep
from pandas import DataFrame
import time
import numpy as np
from pathlib import Path
import os

if __name__ == "__main__":
  el.experiment.run()


def set(args):
  experiment = el.experiment.Experiment()
  experiment.project.name = os.path.basename(__file__)[:-3]
  experiment.path.output = '/tmp/'+experiment.project.name+'/'
  experiment.setPath()

  experiment.factor.xp1 = el.factor.Factor()
  experiment.factor.xp1.method = ['methodOne']
  experiment.factor.xp1.parameterMethodOne = ['modalityOne', 'modalityTwo']
  experiment.factor.xp2 = el.factor.Factor()
  experiment.factor.xp2.method = ['methodTwo']
  experiment.factor.xp2.parameterMethodTwo = np.arange(5)

  # experiment.factor.truc = el.factor.Factor() #['machin', 'bidule']

  experiment.metric.m = ['mean']

  return experiment

def step(setting, experiment):
  print(setting.id())
  np.save(experiment.path.output+setting.id()+'_m.npy', 0)
