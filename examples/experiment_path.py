import explanes as el
import os

e=el.Experiment()
e.project.name = 'experiment'
e.path.processing = '/tmp/'+e.project.name+'/processing'
e.path.output = '/tmp/'+e.project.name+'/output'
e.setPath()
print(os.listdir('/tmp/'+e.project.name))
