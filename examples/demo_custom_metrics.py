import doce
import numpy as np
from pathlib import Path

# Let us assume that we want to reduce a metric that is represented as a matrix using the following directive: that the minimal value of each row and compute the average of those minimal values.

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main()

# define the doce environnment
def set(args=None):
  # define the experiment
  experiment = doce.Experiment(
    name = 'custom_metrics',
    purpose = 'demonstrate custom metric reduction directives',
    author = 'john doe',
    address = 'john.doe@no-log.org',
  )

# set acces paths (here only storage is needed)
  experiment.setPath('output', '/tmp/'+experiment.name+'/', force=True)

  # set the plan (factor : modalities)
  experiment.addPlan('plan',
    factor = ['modality'],
  )
  # set the metrics
  experiment.setMetrics(
    m = [
    'min', # mimimal value of the flattened array
    'mean', # average value of the flattened array
    'mean|min', # average of the mimimal value of the flattened array (same as min, since the output of min is scalar)
    'mean_min' # defined below
    ]
  )
  return experiment

def step(setting, experiment):
    # metric is a matrix of 3 rows of 10 values
    metric =[
        np.linspace(2, 10),
        np.linspace(2, 10)+2,
        np.linspace(2, 10)+4]
    np.save(experiment.path.output+setting.id()+'_m.npy', metric)

def mean_min(data): # average over the minimal values of each row
    return np.mean(np.min(data, axis = 1))
