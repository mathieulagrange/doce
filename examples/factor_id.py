import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b']
f.two = [0, 1]
f.three = ['none', 'c']

print(f.id())

for setting in f.mask([0, 1, 1]):
  print(setting.id())
  print(setting.id('list'))
  print(setting.id('hash'))
  print(setting.id(sort=False))
  print(setting.id(separator=' '))
  print(setting.id(hideFactor=['one', 'three']))

print('//')
for setting in f.mask([0, 0, 0]):
  print(setting.id())
  print(setting.id(hideNonAndZero=False))
print('//')

f.default('one', 'a')
for setting in f.mask([0, 1, 1]):
  print(setting.id())
  print(setting.id(hideDefault=False))

f.optional_parameter = ['method_one', 'method_two']
for setting in f.mask([0, 1, 1]):
  print(setting.id(format = 'shortUnderscore'))
delattr(f, 'optional_parameter')
f.optionalParameter = ['methodOne', 'methodTwo']
for setting in f.mask([0, 1, 1]):
  print(setting.id(format = 'shortCapital'))
