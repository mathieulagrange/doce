import sys
import re

def constantColumn(
  table=None
):
  """Store which column(s) have the same value for all lines.

	Parameters
	----------

  table : list of equal size lists or None
    table of literals

	Returns
	-------

  indexes :
    indexes of constant valued columns

  values :
    values of the constant valued columns

	See Also
	--------

	Examples
	--------

  """

  indexes = [True] * len(table[0])
  values = [None] * len(table[0])

  for r in table:
      for cIndex, c in enumerate(r):
          if values[cIndex] == None:
              values[cIndex] = c
          elif values[cIndex] != c:
              indexes[cIndex] = False
  return (indexes, values)

def compressName(f, format):
  """.

	Parameters
	----------

	Returns
	-------

	See Also
	--------

	Examples
	--------

  """
  sf = f
  if 'shortUnderscore' in format:
    sf = ''.join([itf[0] for itf in f.split('_')])
  if 'shortCapital' in format:
    sf = f[0]+''.join([itf[0] for itf in re.findall('[A-Z][^A-Z]*', f)]).lower()
  return sf

def query_yes_no(question, default="yes"):
  """Ask a yes/no question via input() and return their answer.

  "question" is a string that is presented to the user.
  "default" is the presumed answer if the user just hits <Enter>.
      It must be "yes" (the default), "no" or None (meaning
      an answer is required of the user).

  The "answer" return value is True for "yes" or False for "no".
  """
  valid = {"yes": True, "y": True, "ye": True,
           "no": False, "n": False}
  if default is None:
    prompt = " [y/n] "
  elif default == "yes":
    prompt = " [Y/n] "
  elif default == "no":
    prompt = " [y/N] "
  else:
    raise ValueError("invalid default answer: '%s'" % default)

  while True:
    sys.stdout.write(question + prompt)
    choice = input().lower()
    if default is not None and choice == '':
      return valid[default]
    elif choice in valid:
      return valid[choice]
    else:
      sys.stdout.write("Please respond with 'yes' or 'no' "
                           "(or 'y' or 'n').\n")


def runFromNoteBook():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

def runFromColab():
    try:
        import google.colab
        return True
    except:
        return False
