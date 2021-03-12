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

def run():
  """This method shall be called from the main script of the experiment to control the experiment using the command line.

  This method provides a front-end for running an explanes experiment. It should be called from the main script of the experiment. The main script must define a **set** function that will be called before processing and a **step** function that will be processed for each setting. It may also define a **display** function that will used to monitor the results.

  Examples

  Assuming that the file experiment_run.py contains:

  >>> import doce
  >>> if __name__ == "__main__":
  ...   doce.experiment.run() # doctest: +SKIP
  >>> def set(experiment, args=None):
  ...   experiment.factor.factor1=[1, 3]
  ...   experiment.factor.factor2=[2, 4]
  ...   return experiment
  >>> def step(setting, experiment):
  ...   print(setting.id())

  Executing this file with the --run option gives::

  $ python experiment_run.py -r
   factor1_1_factor2_2
   factor1_1_factor2_4
   factor1_3_factor2_2
   factor1_3_factor2_4

  Executing this file with the --help option gives::

  $ python experiment_run.py -h

  usage: experiment_run.py [-h] [-i] [-f] [-l] [-m MASK] [-M [MAIL]] [-C] [-S]
                         [-s SERVER] [-d [DISPLAY]] [-r [RUN]] [-D] [-v] [-P]
                         [-R [REMOVE]] [-K [KEEP]]

optional arguments:
  -h, --help            show this help message and exit
  -i, --information     show information about the experiment
  -f, --factor          show the factors of the experiment
  -l, --list            list settings
  -m MASK, --mask MASK  mask of the experiment to run
  -M [MAIL], --mail [MAIL]
                        send email at the beginning and end of the
                        computation. If a positive integer value x is
                        provided, additional emails are sent every x hours.
  -C, --copy            copy codebase to server defined by -s argument
  -S, --serverDefault   augment the command line with the content of the dict
                        experiment._defaultServerRunArgument
  -s SERVER, --server SERVER
                        running server side. Integer defines the index in the
                        host array of config. -2 (default) runs attached on
                        the local host, -1 runs detached on the local host, -3
                        is a flag meaning that the experiment runs serverside
  -d [DISPLAY], --display [DISPLAY]
                        display metrics. If no parameter is given, consider
                        the default display and show all metrics. If the str
                        parameter contain a list of integers, use the default
                        display and show only the selected metrics defined by
                        the integer list. If the str parameter contain a name,
                        run the display method with this name.
  -r [RUN], --run [RUN]
                        perform computation. Integer parameter sets the number
                        of jobs computed in parallel (default to one core).
  -D, --debug           debug mode
  -v, --version         print version
  -P, --progress        display progress bar
  -R [REMOVE], --remove [REMOVE]
                        remove the selected settings from a given path (all
                        paths of the experiment by default, if the argument
                        does not have / or \, the argument is interpreted as a
                        member of the experiments path)
  -K [KEEP], --keep [KEEP]
                        keep only the selected settings from a given path (all
                        paths of the experiment by default, if the argument
                        does not have / or \, the argument is interpreted as a
                        member of the experiments path)

  """

  parser = argparse.ArgumentParser()
  parser.add_argument('-e', '--experiment', type=str, help='select experiment', default='all')
  parser.add_argument('-i', '--information', help='show information about the experiment', action='store_true')
  parser.add_argument('-f', '--factor', help='show the factors of the experiment', action='store_true')
  parser.add_argument('-l', '--list', help='list settings', action='store_true')
  parser.add_argument('-m', '--mask', type=str, help='mask of the experiment to run', default='[]')
  parser.add_argument('-M', '--mail', help='send email at the beginning and end of the computation. If a positive integer value x is provided, additional emails are sent every x hours.', nargs='?', default='-1')
  parser.add_argument('-C', '--copy', help='copy codebase to server defined by the server (-s) argument', action='store_true')
  parser.add_argument('-S', '--serverDefault', help='augment the command line with the content of the dict experiment._defaultServerRunArgument', action='store_true')
  parser.add_argument('-s', '--server', type=int, help='running server side. Integer defines the index in the host array of config. -2 (default) runs attached on the local host, -1 runs detached on the local host, -3 is a flag meaning that the experiment runs serverside', default=-2)
  parser.add_argument('-d', '--display', type=str, help='display metrics. If no parameter is given, consider the default display and show all metrics. If the str parameter contain a list of integers, use the default display and show only the selected metrics defined by the integer list. If the str parameter contain a name, run the display method with this name.', nargs='?', default='-1')
  parser.add_argument('-E', '--export', type=str, help='Export the display of reduced metrics among different file types (html, png, pdf). If parameter is empty, all exports are made. If parameter has a dot, interpreted as a filename which should be of support type. If parameter has nothing before the dot, interpreted as file type, and experiment.project.name is used. If parameter has no dot, interpreted as file name with no extension, and all exports are made', nargs='?', default='none')
  parser.add_argument('-r', '--run', type=int, help='perform computation. Integer parameter sets the number of jobs computed in parallel (default to one core).', nargs='?', const=1)
  parser.add_argument('-D', '--debug', help='debug mode', action='store_true')
  parser.add_argument('-v', '--version', help='print version', action='store_true')
  parser.add_argument('-P', '--progress', help='display progress bar', action='store_true')
  parser.add_argument('-R', '--remove', type=str, help='remove the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-A', '--archive', type=str, help='archive the selected  settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. The files are copied to the path experiment.path.archive if set.', nargs='?', const='')
  parser.add_argument('-K', '--keep', type=str, help='keep only the selected settings from a given path. If the argument does not have / or \, the argument is interpreted as a member of the experiments path. Unwanted files are moved to the path experiment.path.archive if set, deleted otherwise.', nargs='?', const='')
  parser.add_argument('-p', '--parameter', type=str, help='a dict specified as str (for example, \'{\"test\": 1}\') that will be available in Experiment.parameter (parameter.test 1)', default='{}')

  args = parser.parse_args()

  if args.version:
    print("Experiment version "+experiment.project.version)
    exit(1)
  if args.mail is None:
    args.mail = 0
  else:
    args.mail = float(args.mail)

  if args.export is None:
    args.export = 'all'

  mask = ast.literal_eval(args.mask)
  parameter = ast.literal_eval(args.parameter)

  module = sys.argv[0][:-3]
  try:
    config = importlib.import_module(module)
  except:
   print('Please provide a valid project name')
   raise ValueError

  experiment = doce.experiment.Experiment()
  if isinstance(parameter, dict):
    experiment.parameter = parameter

  experiment = config.set(experiment)
  experiment.mask = mask
  experiment.status.debug = args.debug

  if args.experiment != 'all':
    if hasattr(experiment.factor, args.experiment):
      experiment.factor = getattr(experiment.factor, args.experiment)
    else:
      print('Unrecognized experiment: '+args.experiment)
  elif len(experiment.factor.factors())>0 and isinstance(getattr(experiment.factor, experiment.factor.factors()[0]), doce.factor.Factor):
    experiment.factor = experiment.factor.merge()
  if args.serverDefault:
    args.serverDefault = False
    for key in experiment._defaultServerRunArgument:
      # args[key] =
      args.__setattr__(key, experiment._defaultServerRunArgument[key])

  if args.information:
      print(experiment)
  if args.factor:
      print(experiment.factor.asPandaFrame())
  if args.list:
    print(experiment.factor.constantFactors(experiment.mask))
    experiment.do(experiment.mask, progress=False)

  if args.remove:
    experiment.cleanDataSink(args.remove, experiment.mask, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, debug=experiment.status.debug)
  if args.keep:
    experiment.cleanDataSink(args.keep, experiment.mask, reverse=True, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, debug=experiment.status.debug)
  if args.archive:
    if experiment.path.archive:
      experiment.cleanDataSink(args.archive, experiment.mask, keep=True, settingEncoding=experiment._settingEncoding, archivePath=experiment.path.archive, debug=experiment.status.debug)
    else:
      print('Please set the path.archive path before issuing an archive command.')

  logFileName = ''
  if args.server>-2:
    unparser = argunparse.ArgumentUnparser()
    kwargs = copy.deepcopy(vars(args))
    kwargs['server'] = -3
    command = unparser.unparse(**kwargs).replace('\'', '\"').replace('\"', '\\\"')
    if args.debug:
      command += '; bash '
    command = 'screen -dm bash -c \'python3 '+experiment.project.name+'.py '+command+'\''
    message = 'experiment launched on local host'
    if args.server>-1:
      if args.copy:
        syncCommand = 'rsync -r '+experiment.path.code+'* '+experiment.host[args.server]+':'+experiment.path.code_raw
        print(syncCommand)
        os.system(syncCommand)
      command = 'ssh '+experiment.host[args.server]+' "cd '+experiment.path.code_raw+'; '+command+'"'
      message = 'experiment launched on host: '+experiment.host[args.server]
    print(command)
    os.system(command)
    print(message)
    exit()

  if args.server == -3:
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.status.runId+'.txt'
  if args.mail>-1:
    experiment.sendMail(args.mask+' has started.', '<div> Mask = '+args.mask+'</div>')
  if args.run and hasattr(config, 'step'):
    experiment.do(mask, config.step, nbJobs=args.run, logFileName=logFileName, progress=args.progress, mailInterval = float(args.mail))


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

  body = '<div> Mask = '+args.mask+'</div>'
  if display:
    if hasattr(config, displayMethod):
      getattr(config, displayMethod)(experiment, experiment.factor.mask(experiment.mask))
    else:
      (df, header, styler) = dataFrameDisplay(experiment, args, config, selectDisplay, selectFactor)
      print(header)
      print(df)
      if args.export != 'none':
        exportDataFrame(experiment, args, df, styler)
      if args.mail>-1:
        body += '<div> '+header+' </div><br>'+styler.render()

  if args.server == -3:
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.status.runId+'.txt'
    if os.path.exists(logFileName):
      with open(logFileName, 'r') as file:
        log = file.read()
        if log:
          body+= '<h2> Error log </h2>'+log.replace('\n', '<br>')

  if args.mail>-1:
    experiment.sendMail(args.mask+' is over.', body) #

def dataFrameDisplay(experiment, args, config, selectDisplay, selectFactor):

  mask = experiment.mask
  ma=copy.deepcopy(mask)
  if selectFactor:
    # print('pass')
    # print(experiment.factor.factors())
    fi = experiment.factor.factors().index(selectFactor)
    mask = doce.util.expandMask(mask, selectFactor, experiment.factor)
    ma=copy.deepcopy(mask)
    ma[fi]=mask[fi][0]
    # print(ma)

  (table, columns, header, nbFactorColumns) = experiment.metric.reduce(experiment.factor.mask(ma), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, settingEncoding = experiment._settingEncoding, verbose=args.debug, reductionDirectiveModule=config)


  if selectFactor:
    modalities = getattr(experiment.factor, selectFactor)
    header = 'metric: '+columns.pop()+' '+header.replace(selectFactor+': '+str(modalities[0])+' ', '')

    columns.append(modalities[ma[fi]])

    for m in range(1, len(mask[fi])):
      ma[fi]=mask[fi][m]
      (sd, ch, csd, nb)  = experiment.metric.reduce(experiment.factor.mask(ma), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, settingEncoding = experiment._settingEncoding, verbose=args.debug, reductionDirectiveModule=config)
      columns.append(modalities[ma[fi]])
      for s in range(len(sd)):
        table[s].append(sd[s][-1])
    #
    # (table, columns, header, nbFactorColumns) = experiment.metric.reduce(experiment.factor.mask(experiment.mask), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, settingEncoding = experiment._settingEncoding, verbose=args.debug, reductionDirectiveModule=config)


  df = pd.DataFrame(table, columns=columns).fillna('')
  # df[columns[nbFactorColumns+2:]] = df[columns[nbFactorColumns+2:]].round(experiment._display.metricPrecision)
  # pd.set_option('precision', experiment._display.metricPrecision)

  if selectDisplay and not selectFactor and  len(columns)>=max(selectDisplay)+nbFactorColumns:
    selector = [columns[i] for i in [*range(nbFactorColumns)]+[s+nbFactorColumns for s in selectDisplay]]
    df = df[selector]

  d = dict(selector="th", props=[('text-align', 'center'), ('border-bottom', '.1rem solid')])

  # Construct a mask of which columns are numeric
  numeric_col_mask = df.dtypes.apply(lambda d: issubclass(np.dtype(d).type, np.number))
  cPercent = []
  cNoPercent = []
  cMinus = []
  cNoMinus = []
  precisionFormat = {}
  for ci, c in enumerate(columns):
    if ci >= nbFactorColumns:
      if '%' in c:
        precisionFormat[c] = '{0:.'+str(experiment._display.metricPrecision-2)+'f}'
        cPercent.append(c)
      else:
        precisionFormat[c] = '{0:.'+str(experiment._display.metricPrecision)+'f}'
        cNoPercent.append(c)
      if '-' in c:
        cMinus.append(c)
      else:
        cNoMinus.append(c)
  # print(precisionFormat)
  # form = '{0:.'+str(experiment._display.metricPrecision-2)+'f}'
  # df[df.columns[cPercent]]= df[df.columns[cPercent]].applymap(lambda x: np.round(x, experiment._display.metricPrecision-2)) # form.format
  # form = '{0:.'+str(experiment._display.metricPrecision)+'f}'
  # df[df.columns[cNoPercent]]= df[df.columns[cNoPercent]].applymap(lambda x: np.round(x, experiment._display.metricPrecision)) # form.format
  # print(cPercent)
  # print([experiment._display.metricPrecision-2]*len(cPercent))
  dPercent = pd.Series([experiment._display.metricPrecision-2]*len(cPercent), index=cPercent)
  dNoPercent = pd.Series([experiment._display.metricPrecision]*len(cNoPercent), index=cNoPercent)
  df=df.round(dPercent).round(dNoPercent)
  form = '%.'+str(experiment._display.metricPrecision)+'f'
  # print(form)
  pd.set_option('display.float_format', lambda x: '%.0f' % x
                      if (x == x and x*10 % 10 == 0)
                      else form % x)

  styler = df.style.set_properties(subset=df.columns[numeric_col_mask], # right-align the numeric columns and set their width
        **{'width':'10em', 'text-align':'right'})\
        .set_properties(subset=df.columns[~numeric_col_mask], # left-align the non-numeric columns and set their width
        **{'width':'10em', 'text-align':'left'})\
        .set_properties(subset=df.columns[nbFactorColumns], # left-align the non-numeric columns and set their width
        **{'border-left':'.1rem solid'})\
        .set_table_styles([d]).format(precisionFormat)
  if not experiment._display.showRowIndex:
    styler.hide_index()
  if experiment._display.bar:
    styler.bar(subset=df.columns[nbFactorColumns:], align='mid', color=['#d65f5f', '#5fba7d'])
  if experiment._display.highlight:
    styler.apply(highlightMax, subset=cNoMinus, axis=0)
    styler.apply(highlightMin, subset=cMinus, axis=0)

  return (df, header, styler)

def highlightMax(s):
  is_max = s == s.max()
  return ['font-weight: bold' if v else '' for v in is_max]
def highlightMin(s):
  is_min = s == s.min()
  return ['font-weight: bold' if v else '' for v in is_min]


def exportDataFrame(experiment, args, df, styler):
  if not os.path.exists('export'):
    os.makedirs('export')
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
  exportFileName = 'export/'+exportFileName
  reloadHeader =  '<script> window.onblur= function() {window.onfocus= function () {location.reload(true)}}; </script>'
  with open(exportFileName+'.html', "w") as outFile:
    outFile.write(reloadHeader)
    outFile.write(styler.render())

  if 'tex' in args.export or 'all' == args.export:
    # columnFormat = ''
    # for n in numeric_col_mask:
    #   if n:
    #     columnFormat+='r'
    #   else:
    #     columnFormat+='l'
    df.to_latex(buf=exportFileName+'.tex', index=experiment._display.showRowIndex, bold_rows=True)
    # column_format=columnFormat,

  if 'png' in args.export or 'all' == args.export:
      if shutil.which('wkhtmltoimage') is not None:
        subprocess.call(
        'wkhtmltoimage -f png --width 0 '+exportFileName+'.html '+exportFileName+'.png', shell=True)
      else:
        print('generation of png is handled by converting the html generated from the result dataframe using the wkhtmltoimage tool. This tool must be installed and reachable from you path.')
  if 'pdf' in args.export or 'all' == args.export:
    # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless --print-to-pdf=testChrome.pdf cds.html --print-to-pdf-no-header
    # if shutil.which('chromium'):
    #   subprocess.call('chromium --headless --print-to-pdf-no-header --print-to-pdf='+exportFileName+'.pdf '+exportFileName+'.html', shell=True)
    # el
    if shutil.which('wkhtmltopdf'):
      subprocess.call(
      'wkhtmltopdf '+exportFileName+'.html '+exportFileName+'.pdf', shell=True)
    else:
      print('generation of pdf is handled by converting the html generated from the result dataframe using chrome, chromium or the wkhtmltoimage tool. At least one of those tools must be installed and reachable from you path.')

    if shutil.which('pdfcrop') is not None:
      subprocess.call(
      'pdfcrop '+exportFileName+'.pdf '+exportFileName+'.pdf', shell=True)
    else:
      print('crop of pdf is handled using the pdfcrop tool. This tool must be installed and reachable from you path.')

  if 'html' not in args.export and 'all' != args.export:
    os.remove(exportFileName+'.html')
