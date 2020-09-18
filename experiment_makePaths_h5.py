import explanes as el
import os

e=el.Experiment()
e.project.name = 'experiment'
e.path.processing = '/tmp/'+e.project.name+'/processing/test.h5'
e.path.output = '/tmp/'+e.project.name+'/output'
e.makePaths(force=True)
print(os.listdir('/tmp/'+e.project.name))
