import explanes as el
e=el.experiment.Experiment()
e.factor.factor1=[1, 3]
e.factor.factor2=[2, 4]

# this function displays the sum of the two modalities of the current setting
def myFunction(setting, experiment):
    print('{}+{}={}'.format(setting.factor1, setting.factor2, setting.factor1+setting.factor2))

e.do([], myFunction, nbJobs=1, tqdmDisplay=False)

e.do([], myFunction, nbJobs=3, tqdmDisplay=False)
