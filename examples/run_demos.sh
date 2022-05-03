
for f in *.py
do
  echo "Running $f file..."
  python $f -r -d
done
