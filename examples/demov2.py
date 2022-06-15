import doce
import time
import numpy as np
from pathlib import Path

info = {
  'name': 'demo',
  'purpose': 'hello world of the doce package',
  'author': 'mathieu Lagrange',
  'address': 'mathieu.lagrange@ls2n.fr'
  }

plan = {
  'nn_type': ['cnn', 'lstm'],
  'n_layers': np.arange(2, 10, 3),
  'learning_rate': [0.001, 0.0001, 0.00001],
  'dropout': [0, 1]
  }

metrics = {
  'accuracy': {'output' : 'accuracy', 'percent': True, 'higher_the_better': True}},
  'duration': [np.mean, '*-']
}

experiment = doce.Experiment(
  info = info,
  plans = {'plan':plan},
  metrics = metrics,
  paths = {'output': '/tmp/'+info['name']+'/'})

def step(setting, experiment):
  setting_metrics = {
    'accuracy': np.random.randn(10),
    'duration': np.random.randn(10)
    }
  return setting_metrics

if __name__ == "__main__":
  experiment.cli(step=step)
