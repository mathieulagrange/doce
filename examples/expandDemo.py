import doce
from time import sleep
from pandas import DataFrame
import time
import numpy as np
from pathlib import Path
import copy

if __name__ == "__main__":
  doce.run.run()

def set(args):
  experiment = doce.experiment.Experiment()
  experiment.project.name = 'npyDemo'
  experiment.project.description = 'demonstration of the expand display technique'
  experiment.project.author = 'mathieu Lagrange'
  experiment.project.address = 'mathieu.lagrange@ls2n.fr'
  experiment.project.version = '0.1'

  experiment.path.output = '/tmp/'+experiment.project.name+'/'
  experiment.path.code = '~/tools/explanes.py/demonstrations/'
  experiment.setPath()

  experiment.factor.type = ['float', 'double']
  experiment.factor.size = 1000*np.array([1, 2, 4, 8])
  experiment.factor.loop = [20, 40]

  experiment.metric.duration = ['']
  return experiment

def step(setting, experiment):

  # print(settingMse.shape)
  tic = time.time()
  for r in range(setting.loop):
    M = np.random.random((setting.size, setting.size))

  duration = time.time()-tic
  np.save(experiment.path.output+setting.id()+'_duration.npy', duration)

# uncomment this method to fine tune display of metrics
def myDisplay(experiment, settings):

  factor = 'size'
  fi = settings.factors().index(factor)

  mask = experiment.mask

  if len(mask)<=fi:
    for m in range(1+fi-len(mask)):
      mask.append(-1)

  nm = []
  for mi, m in enumerate(mask):
    if m==-1:
      nm.append(list(range(len(getattr(settings, settings.factors()[mi])))))
    else:
      nm.append(m)
  mask = nm
  print(mask)
  # mask = [-1] * len(settings.factors())
  # mask[fi]=0
  ma=copy.deepcopy(mask)
  ma[fi]=mask[fi][0]
  print('///////')
  print(ma)
  print('///////')
  print(mask)
  (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor)  = experiment.metric.reduce(settings.mask(ma), experiment.path.output)

  constantSettingDescription = 'metric: '+columnHeader.pop()+' '+constantSettingDescription.replace(factor+': '+str(getattr(settings, factor)[0])+' ', '')

  columnHeader.append(getattr(settings, factor)[ma[fi]])

  for m in range(1, len(mask[fi])):
    ma[fi]=mask[fi][m]
    (sd, ch, csd, nb)  = experiment.metric.reduce(settings.mask(ma), experiment.path.output)
    columnHeader.append(getattr(settings, factor)[ma[fi]])
    for s in range(len(sd)):
      settingDescription[s].append(sd[s][-1])


  print(nbColumnFactor) #ok
  print(constantSettingDescription)
  print(columnHeader)
  print(settingDescription)
