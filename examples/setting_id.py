import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b']
f.two = [0, 1]
f.three = ['none', 'c']
f.four = 'd'

print(f)

for setting in f.mask([0, 1, 1]):
  # default display
  print(setting.id())
# list format
print(setting.id('list'))
# hashed version of the default display
print(setting.id('hash'))
# do not apply sorting of the factor
print(setting.id(sort=False))
# specify a separator
print(setting.id(separator=' '))
# do not show some factors
print(setting.id(hideFactor=['one', 'three']))
# do not show factors with only one modality
print(setting.id(singleton=False))

delattr(f, 'four')

for setting in f.mask([0, 0, 0]):
  print(setting.id())
# do not hide the default value in the description
print(setting.id(hideNoneAndZero=False))

# set the default value of factor one to a
f.default('one', 'a')
for setting in f.mask([0, 1, 1]):
  print(setting.id())
# do not hide the default value in the description
print(setting.id(default=True))

f.optional_parameter = ['value_one', 'value_two']
for setting in f.mask([0, 1, 1]):
  print(setting.id())
# compress the names as pythonCase
print(setting.id(format = 'shortUnderscore'))
delattr(f, 'optional_parameter')

f.optionalParameter = ['valueOne', 'valueTwo']
for setting in f.mask([0, 1, 1, 0]):
  print(setting.id())
# compress the names as camelCase
print(setting.id(format = 'shortCapital'))

f.optionalParameter = ['value_one', 'value_two']
for setting in f.mask([0, 1, 1, 0]):
  print(setting.id())
# compress the names with smart detection of the type of case
print(setting.id(format = 'short'))
