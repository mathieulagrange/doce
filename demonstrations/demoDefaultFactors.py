import numpy as np

def set(experiment, args):
  experiment.project.name = 'defaultFactor'
  experiment.project.description = 'demonstration of default usage'
  experiment.project.author = 'mathieu Lagrange'
  experiment.project.address = 'mathieu.lagrange@ls2n.fr'
  experiment.project.version = '0.1'

  experiment.path.output = '/tmp/'+experiment.project.name+'/'
  experiment.path.code = '~/tools/explanes.py/'
  experiment.makePaths()

  experiment.host = ['pc-lagrange.irccyn.ec-nantes.fr']

  experiment.factor.data = ['truc', 'machin', 'bidule']
  experiment.factor.nbRuns = [2000, 4000, 6000]
  # experiment.factor.nb = 4000
  # experiment.factor.test = [0, 10]
  # experiment.factor.test2 = 'none'
  #
  # experiment.factor.setDefault('nbRuns', 2000)
  # experiment.factor.setDefault('test', 10, force=True)
  # experiment.factor.dataType = 'float'

  experiment.metric.m = ['mean']
  experiment._idFormat = {'format': 'long', 'noneAndZero2void': False}
  experiment._factorFormatInReduce = 'shortCapital'
  return experiment

def step(setting, experiment):

  print(setting.getId(**experiment._idFormat))
  np.save(experiment.path.output+setting.getId(**experiment._idFormat)+'_m.npy',  np.random.rand(1, 3))

def display(experiment, settings):
    (data, desc, header)  = experiment.metric.get('m', settings, experiment.path.output, **experiment._idFormat)

    print(header)
    print(desc)
    print(len(data))
