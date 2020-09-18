import explanes as el
e=el.experiment.Experiment()
e.path.output = '/tmp/test'
e.makePaths()
e.cleanExperiment()
