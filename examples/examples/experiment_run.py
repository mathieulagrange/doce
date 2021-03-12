import explanes as el

if __name__ == "__main__":
  el.experiment.run()

def set(args):
  experiment = el.Experiment()
  experiment.factor.factor1=[1, 3]
  experiment.factor.factor2=[2, 4]
  return experiment

def step(setting, experiment):
  print(setting)
