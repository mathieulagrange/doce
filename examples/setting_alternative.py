import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b', 'c']
f.two = [1, 2, 3]

for setting in f.mask([1, 1]):
  # the inital setting
  print(setting)
# the same setting but with the factor 'two' set to modality 1
print(setting.alternative('two', value=1))
# the same setting but with the first factor set to modality 1
print(setting.alternative(1, value=1))
# the same setting but with the factor 'two' set to modality index 0
print(setting.alternative('two', positional=0))
# the same setting but with the factor 'two' set to modality of relative index -1 with respect to the modality index of the current setting
print(setting.alternative('two', relative=-1))
