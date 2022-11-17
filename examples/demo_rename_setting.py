import doce
import numpy as np

# define the experiment
experiment = doce.Experiment(
  name = 'demo_rename_setting',
  purpose = 'renaming settings for access to output of other settings',
  author = 'mathieu Lagrange',
  address = 'mathieu.lagrange@ls2n.fr',
)
# set acces paths (here only storage is needed)
experiment.set_path('output', '/tmp/'+experiment.name+'/', force=True)
# set the "svm" plan
experiment.add_plan('reference',
  classifier = ['oracle', 'chance'],
  step = ['compute', 'metric']
)

experiment.add_plan('deep',
  classifier = ['cnn'],
  step = ['compute', 'metric'],
  n_layers = [2, 4, 8],
  dropout = [0, 1]
)

experiment.set_metric(
  name = 'difference',
  percent=True,
  higher_the_better= True,
  significance = True
)

def step(setting, experiment):
  # the accuracy  is a function of cnn_type, and use of dropout
  if setting.step == 'compute':
    prediction = np.random.random_sample(10)/6
    np.save(experiment.path.output+setting.identifier()+'_prediction.npy', prediction)
  elif setting.step == 'metric':
    prediction_file_name = setting.replace('step', 'compute').identifier()+'_prediction.npy'
    print(prediction_file_name)
    prediction = np.load(experiment.path.output+prediction_file_name)
    prediction_reference_file_name = doce.Setting(experiment.reference, [0, 0]).identifier()+'_prediction.npy'
    print(prediction_reference_file_name)
    prediction_reference = np.load(experiment.path.output+prediction_reference_file_name)
    difference = np.abs(prediction_reference-prediction)
    np.save(experiment.path.output+setting.identifier()+'_difference.npy', difference)

# invoke the command line management of the doce package
if __name__ == "__main__":
  doce.cli.main(experiment = experiment, func=step)
