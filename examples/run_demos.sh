
#!/bin/bash
for f in *.py
do
  echo "Running ${f%???} ..."
  python $f -c -d
done
