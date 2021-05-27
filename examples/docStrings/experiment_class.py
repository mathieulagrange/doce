import explanes as el
e=el.experiment.Experiment()
e.specificInfo = 'stuff'
import types
e.myData = types.SimpleNamespace()
e.myData.info1= 1
e.myData.info2= 2
print(e)

e.specificInfo = 'stuff'
import types
e.myData = types.SimpleNamespace()
e.myData.info1= 1
e.myData.info2= 2
print(e)
