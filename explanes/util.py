import sys
import re


def constantColumn(
  table=None
):
  """detect which column(s) have the same value for all lines.


	Parameters
	----------

  table : list of equal size lists or None
    table of literals.

	Returns
	-------

  values : list of literals
    values of the constant valued columns, None if the column is not constant.

	Examples
	--------
  >>> import explanes as el
  >>> table = [['a', 'b', 1, 2], ['a', 'c', 2, 2], ['a', 'b', 2, 2]]
  >>> el.util.constantColumn(table)
  ['a', None, None, 2]
  """

  indexes = [True] * len(table[0])
  values = [None] * len(table[0])

  for r in table:
      for cIndex, c in enumerate(r):
          if values[cIndex] is None and indexes[cIndex]:
              values[cIndex] = c
          elif values[cIndex] != c:
              indexes[cIndex] = False
              values[cIndex] = None
  return values

def pruneSettingDescription(settingDescription, columnHeader=None, nbColumnFactor=0, factorDisplay='long'):
  """remove the columns corresponding to factors with only one modality from the settingDescription and the columnHeader.

  Remove the columns corresponding to factors with only one modality from the settingDescription and the columnHeader and describes the factors with only one modality in a separate string.

	Parameters
	----------

  settingDescription: list of list of literals
    the body of the table.

  columnHeader: list of string (optional)
    the column header of the table.

  nbColumnFactor: int (optional)
    the number of columns corresponding to factors (default 0).

  factorDisplay:
    type of description of the factors (default 'long'), see :meth:`explanes.util.compressDescription` for reference.

	Returns
	-------

  settingDescription: list of list of literals
    settingDescription where the columns corresponding to factors with only one modality are removed.

  columnHeader: list of str
    columnHeader where the columns corresponding to factors with only one modality are removed.

  constantSettingDescription: str
    description of the settings with constant modality.

  nbColumnFactor: int
    number of factors in the new settingDescription.

	Examples
	--------
  >>> import explanes as el

  >>> header = ['factor_1', 'factor_2', 'metric_1', 'metric_2']
  (settingDescription, columnHeader, constantSettingDescription, >>> table = [['a', 'b', 1, 2], ['a', 'c', 2, 2], ['a', 'b', 2, 2]]
  >>> nbColumnFactor) = el.util.pruneSettingDescription(table, header, 2)
  >>> print(nbColumnFactor)
  1
  >>> print(constantSettingDescription)
  factor_1: a
  >>> print(columnHeader)
  ['factor_2', 'metric_1', 'metric_2']
  >>> print(settingDescription)
  [['b', 1, 2], ['c', 2, 2], ['b', 2, 2]]
  """
  constantSettingDescription = ''
  if nbColumnFactor == 0:
    nbColumnFactor = len(settingDescription[0])
  if settingDescription:
    if len(settingDescription)>1:
      constantValue = constantColumn(settingDescription)
      for si, s in enumerate(constantValue):
        if not columnHeader and si>0 and s is None:
          constantValue[si-1] = None
      ccIndex = [i for i, x in enumerate(constantValue) if x and i<nbColumnFactor]
      nbColumnFactor -= len(ccIndex)
      for s in ccIndex:
        if columnHeader:
          constantSettingDescription += compressDescription(columnHeader[s], factorDisplay)+': '+str(constantValue[s])+' '
        else:
          constantSettingDescription += settingDescription[0][s]+' '
      for s in sorted(ccIndex, reverse=True):
        if columnHeader:
          columnHeader.pop(s)
        for r in settingDescription:
          r.pop(s)
    else:
      constantSettingDescription = ' '.join(settingDescription[0])
  return (settingDescription, columnHeader, constantSettingDescription, nbColumnFactor)


def compressDescription(
  description,
  format='long',
  atomLength=2
  ):
  """ reduces the number of letters for each word in a given description structured with underscores (pythonCase) or capital letters (camelCase).

	Parameters
	----------
  description : str
    the structured description.

  format : str, optional
    can be 'long' (default), do not lead to any reduction, 'shortUnderscore' assumes pythonCase delimitation, 'shortCapital' assumes camelCase delimitation, and 'short' attempts to perform reduction by guessing the type of delimitation.

	Returns
	-------

  compressedDescription : str
    The compressed description.

	Examples
	--------

  >>> import explanes as el
  >>> el.util.compressDescription('myVeryLongParameter', format='short')
  myvelopa
  >>> el.util.compressDescription('that_very_long_parameter', format='short', atomLength=3)
  thaverlonpar
  """

  if format == 'short':
    if '_' in description and not description.islower() and not description.isupper():
      print('The description '+description+' has underscores and capital. Explicitely states which delimeter shall be considered for reduction.')
      raise ValueError
    elif '_' in description:
      format = 'shortUnderscore'
    else:
      format = 'shortCapital'
  compressedDescription = description
  if 'shortUnderscore' in format:
    compressedDescription = ''.join([itf[0:atomLength] for itf in description.split('_')])
  if 'shortCapital' in format:
    compressedDescription = description[0:atomLength]+''.join([itf[0:atomLength] for itf in re.findall('[A-Z][^A-Z]*', description)]).lower()
  return compressedDescription

def query_yes_no(
  question,
  default="yes"
  ):
  """ask a yes/no question via input() and return their answer.

  The 'answer' return value is True for 'yes' or False for 'no'.

	Parameters
	----------

  question : str
    phrase presented to the user.
  default : str or None (optional)
    presumed answer if the user just hits <Enter>. It must be 'yes' (default), 'no' or None. The latter meaning an answer is required of the user.

	Returns
	-------

  answer : bool
    True if prompt is 'yes'.

    False if prompt is 'no'.
  """

  valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
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


def inNotebook():
  """detect if the experiment is running from Ipython notebook.
  """
  try:
    __IPYTHON__
    return True
  except NameError:
    return False
