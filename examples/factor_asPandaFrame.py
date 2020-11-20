import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b']
f.two = list(range(10))

print(f)

print(f.asPandaFrame())
