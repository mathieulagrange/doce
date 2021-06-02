import doce
import sys
import pandas as pd
import argparse
import argunparse
import ast
import importlib
import os
import copy
import subprocess
import numpy as np
import shutil
import time
import re

def run():
  """This method shall be called from the main script of the experiment to control the experiment using the command line.

  This method provides a front-end for running an explanes experiment. It should be called from the main script of the experiment. The main script must define a **set** function that will be called before processing and a **step** function that will be processed for each setting. It may also define a **display** function that will used to monitor the results. This main script can define any functions that can be used within the **set**, **step**, and **display** functions.

  Examples

  Assuming that the file experiment_run.py contains:

  >>> import doce
  >>> if __name__ == "__main__":
  ...   doce.experiment.run() # doctest: +SKIP
  >>> def set(experiment, args=None):
  ...   experiment._plan.factor1=[1, 3]
  ...   experiment._plan.factor2=[2, 4]
  ...   return experiment
  >>> def step(setting, experiment):
  ...   print(setting.id())

  Executing this file with the --run option gives:

  $ python experiment_run.py -r
   factor1_1_factor2_2
   factor1_1_factor2_4
   factor1_3_factor2_2
   factor1_3_factor2_4

  Executing this file with the --help option gives:

  $ python experiment_run.py -h

    usage: npyDemo.py [-h] [-A [ARCHIVE]] [-C] [-d [DISPLAY]] [-D] [-e [EXPERIMENT]] [-E [EXPORT]] [-f] [-i] [-K [KEEP]] [-l] [-M [MAIL]] [-p userData] [-P [PROGRESS]] [-r [RUN]] [-R [REMOVE]] [-s SERVER] [-S] [-v]

  optional arguments:
    -h, --help
      show this help message and exit.
    -A [ARCHIVE], --archive [ARCHIVE]
      archive the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. The files are copied to the path experiment.path.archive if set.
    -C, --copy
      copy codebase to server defined by the server (-s) argument.
    -d [DISPLAY], --display [DISPLAY]
      display metrics. If no parameter is given, consider the default display and show all metrics. If the str parameter contain a list of integers, use the default display and show only the selected metrics defined by the integer list. If the str parameter contain a name, run the display method with this name.
    -e [EXPERIMENT], --experiment [EXPERIMENT]
        select experiment. List experiments if empty.
    -E [EXPORT], --export [EXPORT]
        export the display of reduced metrics among different file types (html, png, pdf). If parameter is empty, all exports are made. If parameter has a dot, interpreted as a filename which should be of support type. If parameter has nothing before the dot, interpreted as file type, and experiment.project.name is used. If parameter has no dot, interpreted as file name with no extension, and all exports are made.
    -f, --factor
      show the factors of the experiment.
    -H HOST, --host HOST
      running on specified HOST. Integer defines the index in the host array of config. -2 (default) runs attached on the local host, -1 runs detached on the local host, -3 is a flag meaning that the experiment runs serverside.
    -i, --information
      show information about the experiment.
    -K [KEEP], --keep [KEEP]
      keep only the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.
    -l, --list
      list settings.
    -M [MAIL], --mail [MAIL]
      send email at the beginning and end of the computation. If a positive integer value x is provided, additional emails are sent every x hours.
    -p USERDATA, --userData USERDATA
      a dict specified as str (for example, '{"test": 1}') that will be available in Experiment.userData (userData.test 1).
    -P [PROGRESS], --progress [PROGRESS]
      display progress bar. Argument controls the display of the current setting: d alphanumeric description, s numeric selector, ds combination of both (default d).
    -r [RUN], --run [RUN]
      perform computation. Integer parameter sets the number of jobs computed in parallel (default to one core).
    -R [REMOVE], --remove [REMOVE]
      remove the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.
    -s SELECTOR, --select SELECTOR
      selection of settings.
    -S, --serverDefault
      augment the command line with the content of the dict experiment._defaultServerRunArgument.
    -v, --version
      print version.
    -V, --verbose
      level of verbosity (default 0: silent).
  """

  parser = argparse.ArgumentParser()
  parser.add_argument('-A', '--archive', type=str, help='archive the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. The files are copied to the path experiment.path.archive if set.', nargs='?', const='')
  parser.add_argument('-C', '--copy', help='copy codebase to server defined by the server (-s) argument.', action='store_true')
  parser.add_argument('-d', '--display', type=str, help='display metrics. If no parameter is given, consider the default display and show all metrics. If the str parameter contain a list of integers, use the default display and show only the selected metrics defined by the integer list. If the str parameter contain a name, run the display method with this name.', nargs='?', default='-1')
  # parser.add_argument('-e', '--experiment', type=str, help='select experiment. List experiments if empty.', nargs='?', default='all')
  parser.add_argument('-E', '--export', type=str, help='Export the display of reduced metrics among different file types (html, png, pdf). If parameter is empty, all exports are made. If parameter has a dot, interpreted as a filename which should be of support type. If parameter has nothing before the dot, interpreted as file type, and experiment.project.name is used. If parameter has no dot, interpreted as file name with no extension, and all exports are made.', nargs='?', default='none')
  parser.add_argument('-H', '--host', type=int, help='running on specified HOST. Integer defines the index in the host array of config. -2 (default) runs attached on the local host, -1 runs detached on the local host, -3 is a flag meaning that the experiment runs serverside.', default=-2)
  parser.add_argument('-i', '--information', help='show information about the experiment.', action='store_true')
  parser.add_argument('-K', '--keep', type=str, help='keep only the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-l', '--list', help='list settings.', action='store_true')
  parser.add_argument('-M', '--mail', help='send email at the beginning and end of the computation. If a positive integer value x is provided, additional emails are sent every x hours.', nargs='?', default='-1')
  parser.add_argument('-p', '--plan', help='show the active plan of the experiment.', action='store_true')
  parser.add_argument('-P', '--progress', help='display progress bar. Argument controls the display of the current setting: d alphanumeric description, s numeric selector, ds combination of both (default d).', nargs='?', const='d')
  parser.add_argument('-r', '--run', type=int, help='perform computation. Integer parameter sets the number of jobs computed in parallel (default to one core).', nargs='?', const=1)
  parser.add_argument('-R', '--remove', type=str, help='remove the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-s', '--select', type=str, help='selection of settings', default='[]')
  parser.add_argument('-S', '--serverDefault', help='augment the command line with the content of the dict experiment._defaultServerRunArgument.', action='store_true')
  parser.add_argument('-u', '--userData', type=str, help='a dict specified as str (for example, \'{\"test\": 1}\') that will be available in Experiment.userData (userData.test=1).', default='{}')
  parser.add_argument('-v', '--version', help='print version', action='store_true')
  parser.add_argument('-V', '--verbose', help='level of verbosity (default 0: silent).', action='store_true')
  args = parser.parse_args()

  if args.version:
    print("Experiment version "+experiment.version)
    exit(1)
  if args.mail is None:
    args.mail = 0
  else:
    args.mail = float(args.mail)

  if args.export is None:
    args.export = 'all'
  if args.progress is None:
    args.progress = ''

  experimentId = 'all'
  selector = re.sub(r"[\n\t\s]*", "", args.select)
  if ':' in selector:
    s = selector.split(':')
    experimentId = s[0]
    if len(s)>1:
      selector = s[1]
    else:
      selector = ''

  try:
    selector = ast.literal_eval(selector)
  except:
    pass


  userData = ast.literal_eval(args.userData)

  module = sys.argv[0][:-3]
  try:
    config = importlib.import_module(module)
  except:
   print('Please provide a valid project name')
   raise ValueError

  # experiment = doce.experiment.Experiment()
  # if isinstance(userData, dict):
  #   experiment.userData = userData

  experiment = config.set(userData)

  experiment.selector = selector

  experiment.status.verbose = args.verbose

  plans = experiment.plans()
  if len(plans)==1:
    experiment._plan = getattr(experiment, plans[0])
  else:
    if experimentId == 'all':
      oPlans = []
      for p in plans:
        oPlans.append(getattr(experiment, p))
      experiment._plan = experiment._plan.merge(oPlans)
    else:
      if experimentId.isnumeric():
        print('pass')
        experimentId = plans[int(experimentId)]
      experiment._plan = getattr(experiment, experimentId)

  # if experimentId != 'all':
  #   if experimentId is None:
  #     for e in :
  #       if isinstance(getattr(self, e), doce.Plan):
  #         print('Selecting plan '+e+': ')
  #         print(getattr(experiment, e))
  #       else:
  #         print('There is only one experiment. Please do not consider the -e (--experiment) option and use -i for information about the factors.')
  #         break
  #   elif hasattr(experiment._plan, experimentId):
  #     experiment._plan = getattr(experiment._plan, experimentId)
  #   else:
  #     print('Unrecognized experiment: '+experimentId)
  # elif len(experiment.plans())>0:

  if args.serverDefault:
    args.serverDefault = False
    for key in experiment._defaultServerRunArgument:
      # args[key] =
      args.__setattr__(key, experiment._defaultServerRunArgument[key])

  if args.information:
      print(experiment)
  if args.plan:
      print(experiment._plan.asPandaFrame())
  if args.list:
    experiment.do(experiment.selector, progress='')

  if args.remove:
    experiment.cleanDataSink(args.remove, experiment.selector, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, verbose=experiment.status.verbose)
  if args.keep:
    experiment.cleanDataSink(args.keep, experiment.selector, reverse=True, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, verbose=experiment.status.verbose)
  if args.archive:
    if experiment.path.archive:
      experiment.cleanDataSink(args.archive, experiment.selector, keep=True, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, verbose=experiment.status.verbose)
    else:
      print('Please set the path.archive path before issuing an archive command.')

  logFileName = ''
  if args.host>-2:
    unparser = argunparse.ArgumentUnparser()
    kwargs = copy.deepcopy(vars(args))
    kwargs['server'] = -3
    command = unparser.unparse(**kwargs).replace('\'', '\"').replace('\"', '\\\"')
    if args.verbose:
      command += '; bash '
    command = 'screen -dm bash -c \'python3 '+experiment.project.name+'.py '+command+'\''
    message = 'experiment launched on local host'
    if args.host>-1:
      if args.copy:
        syncCommand = 'rsync -r '+experiment.path.code+'* '+experiment.host[args.host]+':'+experiment.path.code_raw
        print(syncCommand)
        os.system(syncCommand)
      command = 'ssh '+experiment.host[args.host]+' "cd '+experiment.path.code_raw+'; '+command+'"'
      message = 'experiment launched on host: '+experiment.host[args.host]
    print(command)
    os.system(command)
    print(message)
    exit()

  if args.host == -3:
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.status.runId+'.txt'
  if args.mail>-1:
    experiment.sendMail(args.select+' has started.', '<div> Selector = '+args.select+'</div>')
  if args.run and hasattr(config, 'step'):
    experiment.do(selector, config.step, nbJobs=args.run, logFileName=logFileName, progress=args.progress, mailInterval = float(args.mail))


  selectDisplay = []
  selectFactor = ''
  displayMethod = ''
  display = True
  if args.display == '-1':
    display = False
  elif args.display is not None:
    if  '[' in args.display:
      selectDisplay = ast.literal_eval(args.display)
    elif ',' in args.display:
      s = args.display.split(',')
      selectDisplay = [int(s[0])]
      selectFactor = s[1]
    else:
      displayMethod = args.display

  body = '<div> Selector = '+args.select+'</div>'
  if display:
    if hasattr(config, displayMethod):
      getattr(config, displayMethod)(experiment, experiment._plan.select(experiment.selector))
    else:
      (df, header, styler) = dataFrameDisplay(experiment, args, config, selectDisplay, selectFactor)
      if df is not None:
        print(header)
        pd.set_option('precision', 2)
        print(df)
      if args.export != 'none':
        exportDataFrame(experiment, args, df, styler, header)
      if args.mail>-1:
        body += '<div> '+header+' </div><br>'+styler.render()

  if args.host == -3:
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.status.runId+'.txt'
    if os.path.exists(logFileName):
      with open(logFileName, 'r') as file:
        log = file.read()
        if log:
          body+= '<h2> Error log </h2>'+log.replace('\n', '<br>')

  if args.mail>-1:
    experiment.sendMail(args.select+' is over.', body) #

def dataFrameDisplay(experiment, args, config, selectDisplay, selectFactor):

  selector = experiment.selector
  ma=copy.deepcopy(selector)
  if selectFactor:
    fi = experiment._plan.factors().index(selectFactor)
    selector = experiment._plan.expandSelector(selector, selectFactor)

    # print(selector)
    ms = selector[fi]
    # print(ms)
    selector[fi] = [0]
    experiment._plan.select(selector).__setSettings__()
    settings = experiment._plan._settings
    # print(settings)
    # print(ms)
    for s in settings:
     s[fi] = ms

    # ma=copy.deepcopy(selector)
    # ma[fi]=0

  (table, columns, header, nbFactorColumns, modificationTimeStamp, significance) = experiment.metric.reduce(experiment._plan.select(selector), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, verbose=args.verbose, reductionDirectiveModule=config)

  if len(table) == 0:
      return (None, None, None)
  if selectFactor:
    modalities = getattr(experiment._plan, selectFactor)[ms]
    header = 'metric: '+columns[nbFactorColumns+selectDisplay
    [0]]+' '+header.replace(selectFactor+': '+str(modalities[0])+' ', '')+' '+selectFactor

    columns = columns[:nbFactorColumns]
    for m in modalities:
      columns.append(str(m))
    significance = np.zeros((len(settings), len(modalities)))
    for s in range(len(table)):
      table[s] = table[s][:nbFactorColumns]

    for sIndex, s in enumerate(settings):
      (sd, ch, csd, nb, md, si)  = experiment.metric.reduce(experiment._plan.select(s), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, verbose=args.verbose, reductionDirectiveModule=config)
      modificationTimeStamp += md
      significance[sIndex, :] = si[:, selectDisplay[0]]
      # print(s)
      # print(sd)
      for ssd in sd:
        table[sIndex].append(ssd[1+selectDisplay[0]])

  best = significance == -1
  significance = significance>experiment._display.pValue
  significance = significance.astype(float)
  significance[best] = -1

  if experiment._display.pValue == 0:
    for ti, t in enumerate(table):
      table[ti][-len(significance[ti]):]=significance[ti]

  if modificationTimeStamp:
    print('Displayed data generated from '+ time.ctime(min(modificationTimeStamp))+' to '+ time.ctime(max(modificationTimeStamp)))
    df = pd.DataFrame(table, columns=columns) #.fillna('-')

  if selectDisplay and not selectFactor and  len(columns)>=max(selectDisplay)+nbFactorColumns:
    columns = [columns[i] for i in [*range(nbFactorColumns)]+[s+nbFactorColumns for s in selectDisplay]]
    df = df[columns]

  d = dict(selector="th", props=[('text-align', 'center'), ('border-bottom', '.1rem solid')])

  # Construct a selector of which columns are numeric
  numeric_col_selector = df.dtypes.apply(lambda d: issubclass(np.dtype(d).type, np.number))
  cPercent = []
  cNoPercent = []
  cMinus = []
  cNoMinus = []
  cMetric = []
  precisionFormat = {}
  for ci, c in enumerate(columns):
    if ci >= nbFactorColumns:
      cMetric.append(c)
      if '%' in c:
        precisionFormat[c] = '{0:.'+str(experiment._display.metricPrecision-2)+'f}'
        cPercent.append(c)
      else:
        precisionFormat[c] = '{0:.'+str(experiment._display.metricPrecision)+'f}'
        cNoPercent.append(c)
      if c[-1] == '-' :
        # print('pass')
        cMinus.append(c)
      else:
        cNoMinus.append(c)

  dPercent = pd.Series([experiment._display.metricPrecision-2]*len(cPercent), index=cPercent)
  dNoPercent = pd.Series([experiment._display.metricPrecision]*len(cNoPercent), index=cNoPercent)
  df=df.round(dPercent).round(dNoPercent)

  if cNoPercent:
    form = '%.'+str(experiment._display.metricPrecision)+'f'
  else:
    form = '%.'+str(experiment._display.metricPrecision-2)+'f'

  pd.set_option('display.float_format', lambda x: '%.0f' % x
                      if (x == x and x*10 % 10 == 0)
                      else form % x)

  styler = df.style.set_properties(subset=df.columns[numeric_col_selector], # right-align the numeric columns and set their width
        **{'width':'10em', 'text-align':'right'})\
        .set_properties(subset=df.columns[~numeric_col_selector], # left-align the non-numeric columns and set their width
        **{'width':'10em', 'text-align':'left'})\
        .set_properties(subset=df.columns[nbFactorColumns], # left-align the non-numeric columns and set their width
        **{'border-left':'.1rem solid'})\
        .set_table_styles([d])\
        .format(precisionFormat).applymap(lambda x: 'color: white' if pd.isnull(x) else '')
  if not experiment._display.showRowIndex:
    styler.hide_index()
  if experiment._display.bar:
    styler.bar(subset=df.columns[nbFactorColumns:], align='mid', color=['#d65f5f', '#5fba7d'])
  if experiment._display.highlight:
    styler.apply(highlightStat, subset=cMetric, axis=None, **{'significance':significance})
    styler.apply(highlightBest, subset=cMetric, axis=None, **{'significance':significance})

  return (df.fillna('-'), header, styler)

def highlightStat(s, significance):
  df = pd.DataFrame('', index=s.index, columns=s.columns)
  # print(significance.shape)
  # print(df.shape)
  df = df.where(significance<=0, 'color: blue')
  return df
def highlightBest(s, significance):
  df = pd.DataFrame('', index=s.index, columns=s.columns)
  df = df.where(significance>-1, 'font-weight: bold')
  return df

def exportDataFrame(experiment, args, df, styler, header):
  if not os.path.exists(experiment.path.export):
    os.makedirs(experiment.path.export)
  if args.export == 'all':
    exportFileName = experiment.project.name
  else:
    a = args.export.split('.')
    # print(a)
    if a[0]:
      exportFileName = a[0]
    else:
      exportFileName = experiment.project.name
    if len(a)>1:
      args.export = '.'+a[1]
    else:
      args.export = 'all'
  exportFileName = experiment.path.export+'/'+exportFileName
  reloadHeader =  '<script> window.onblur= function() {window.onfocus= function () {location.reload(true)}}; </script>'
  with open(exportFileName+'.html', "w") as outFile:
    outFile.write(reloadHeader)
    outFile.write('<br><U>'+header+'</U><br><br>')
    outFile.write(styler.render())
  if 'csv' in args.export or 'all' == args.export:
    df.to_csv(path_or_buf=exportFileName+'.csv', index=experiment._display.showRowIndex)
    print('csv export: '+exportFileName+'.csv')
  if 'xls' in args.export or 'all' == args.export:
    df.to_excel(excel_writer=exportFileName+'.xls', index=experiment._display.showRowIndex)
    print('excel export: '+exportFileName+'.xls')

  if 'tex' in args.export or 'all' == args.export:
    df.to_latex(buf=exportFileName+'.tex', index=experiment._display.showRowIndex, bold_rows=True)
    print('tex export: '+exportFileName+'.tex')

  if 'png' in args.export or 'all' == args.export:
      print('Creating image...')
      if shutil.which('wkhtmltoimage') is not None:
        subprocess.call(
        'wkhtmltoimage -f png --width 0 '+exportFileName+'.html '+exportFileName+'.png', shell=True)
        print('png export: '+exportFileName+'.png')
      else:
        print('generation of png is handled by converting the html generated from the result dataframe using the wkhtmltoimage tool. This tool must be installed and reachable from you path.')
  if 'pdf' in args.export or 'all' == args.export:
    print('Creating pdf...')
    if shutil.which('wkhtmltopdf'):
      subprocess.call(
      'wkhtmltopdf '+exportFileName+'.html '+exportFileName+'.pdf', shell=True)
    else:
      print('Generation of pdf is handled by converting the html generated from the result dataframe using the wkhtmltoimage tool which must be installed and reachable from you path.')

    print('Cropping '+exportFileName+'.pdf')
    if shutil.which('pdfcrop') is not None:
      subprocess.call(
      'pdfcrop '+exportFileName+'.pdf '+exportFileName+'.pdf', shell=True)
      print('pdf export: '+exportFileName+'.pdf')
    else:
      print('Crop of pdf is handled using the pdfcrop tool. This tool must be installed and reachable from you path.')

  if 'html' not in args.export and 'all' != args.export:
    os.remove(exportFileName+'.html')
  else:
    print('html export: '+exportFileName+'.html')

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
