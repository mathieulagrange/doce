import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b']
f.two = [1, 2]

print(f.describe())

for setting in f:
  print(setting.describe())
