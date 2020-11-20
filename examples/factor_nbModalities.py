import explanes as el

f = el.factor.Factor()
f.one = ['a', 'b']
f.two = list(range(10))

print(f.nbModalities('one'))
print(f.nbModalities(1))

f = el.factor.Factor()
f.two = list(range(10))
f.one = ['a', 'b']
print(f.nbModalities(1))
