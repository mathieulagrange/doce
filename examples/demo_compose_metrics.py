import doce
import numpy as np
from pathlib import Path

#

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set(args=None):
  # define the experiment
  experiment = doce.Experiment(
    name = 'compose_metrics',
    purpose = 'demonstrate composition of numpy function to build ',
    author = 'mathieu Lagrange',
    address = 'mathieu.lagrange@ls2n.fr',
  )

  # set acces paths (here only storage is needed)
  experiment.setPath('output', '/tmp/'+experiment.name+'/')

  # set the plan (factor : modalities)
  experiment.addPlan('plan',
    factor = ['modality'],
  )
  # set the metrics
  experiment.setMetrics(
    m = [
    'sum', # compute the sum over the flattened array
    'square|sum', # compute the square of the sum over the flattened array
    'sum|square', # compute the sum of the square of the flattened array
    'sqrt|square|sum', # compute the square root of the square of the sum over the flattened array
    ]
  )
  return experiment

def step(setting, experiment):
    # metric is a matrix of 3 rows of 10 values
    m = np.ones((10, 10))*2
    np.save(experiment.path.output+setting.id()+'_m.npy', m)

def mean_min(data): # average over the minimal values of each row
    return np.mean(np.min(data, axis = 1))
