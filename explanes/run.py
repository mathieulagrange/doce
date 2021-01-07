import explanes as el
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

def run():
  """This method shall be called from the main script of the experiment to control the experiment using the command line.

  This method provides a front-end for running an explanes experiment. It should be called from the main script of the experiment. The main script must define a **set** function that will be called before processing and a **step** function that will be processed for each setting. It may also define a **display** function that will used to monitor the results.

  Examples

  Assuming that the file experiment_run.py contains:

  >>> import explanes as el
  >>> if __name__ == "__main__":
  ...   el.experiment.run() # doctest: +SKIP
  >>> def set(experiment, args):
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
  parser.add_argument('-R', '--remove', type=str, help='remove the selected  settings from a given path (all paths of the experiment by default, if the argument does not have / or \, the argument is interpreted as a member of the experiments path)', nargs='?', const='all')
  parser.add_argument('-K', '--keep', type=str, help='keep only the selected settings from a given path (all paths of the experiment by default, if the argument does not have / or \, the argument is interpreted as a member of the experiments path)', nargs='?', const='all')
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

  experiment = el.experiment.Experiment()
  if isinstance(parameter, dict):
    experiment.parameter = parameter

  experiment = config.set(experiment)
  experiment.mask = mask

  if args.experiment != 'all':
    if hasattr(experiment.factor, args.experiment):
      experiment.factor = getattr(experiment.factor, args.experiment)
    else:
      print('Unrecognized experiment: '+args.experiment)
  elif len(experiment.factor.factors())>0 and isinstance(getattr(experiment.factor, experiment.factor.factors()[0]), el.factor.Factor):
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
    experiment.do(experiment.mask, progress=False)

  if args.remove:
    path2clean = args.remove
    if path2clean == 'all':
      experiment.clean(experiment.mask, settingEncoding=experiment._settingEncoding)
    else:
      experiment.cleanDataSink(path2clean, experiment.mask, settingEncoding=experiment._settingEncoding)

  if args.keep:
    path2clean = args.keep
    if path2clean == 'all':
      experiment.clean(experiment.mask, reverse=True, settingEncoding=experiment._settingEncoding)
    else:
      experiment.cleanDataSink(path2clean, experiment.mask, reverse=True, settingEncoding=experiment._settingEncoding)

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
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.project.runId+'.txt'
  if args.mail>-1:
    experiment.sendMail(args.mask+' has started.', '<div> Mask = '+args.mask+'</div>')
  if args.run and hasattr(config, 'step'):
    experiment.do(mask, config.step, nbJobs=args.run, logFileName=logFileName, progress=args.progress, mailInterval = float(args.mail))


  selectDisplay = []
  displayMethod = ''
  display = True
  if args.display == '-1':
    display = False
  elif args.display is not None:
    if '[' in args.display:
      selectDisplay = ast.literal_eval(args.display)
    else:
      displayMethod = args.display

  if display:
    if hasattr(config, displayMethod):
      getattr(config, displayMethod)(experiment, experiment.factor.mask(experiment.mask))
    else:
      dataFrameDisplay(experiment, args, config, selectDisplay)

  if args.server == -3:
    logFileName = '/tmp/explanes_'+experiment.project.name+'_'+experiment.project.runId+'.txt'
    with open(logFileName, 'r') as file:
      log = file.read()
      if log:
        body+= '<h2> Error log </h2>'+log.replace('\n', '<br>')

  if args.mail>-1:
    experiment.sendMail(args.mask+' is over.', body) #

def dataFrameDisplay(experiment, args, config, selectDisplay):

  (table, columns, header, nbFactorColumns) = experiment.metric.reduce(experiment.factor.mask(experiment.mask), experiment.path.output, factorDisplay=experiment._display.factorFormatInReduce, metricDisplay=experiment._display.metricFormatInReduce, factorDisplayLength=experiment._display.factorFormatInReduceLength, metricDisplayLength=experiment._display.metricFormatInReduceLength, settingEncoding = experiment._settingEncoding, verbose=args.debug, reductionDirectiveModule=config)

  df = pd.DataFrame(table, columns=columns).fillna('')
  # df[columns[nbFactorColumns+2:]] = df[columns[nbFactorColumns+2:]].round(experiment._display.metricPrecision)
  # pd.set_option('precision', experiment._display.metricPrecision)

  if selectDisplay and len(columns)>=max(selectDisplay)+nbFactorColumns:
    selector = [columns[i] for i in [*range(nbFactorColumns)]+[s+nbFactorColumns for s in selectDisplay]]
    df = df[selector]

  d = dict(selector="th", props=[('text-align', 'center'), ('border-bottom', '.1rem solid')])
  # Construct a mask of which columns are numeric
  numeric_col_mask = df.dtypes.apply(lambda d: issubclass(np.dtype(d).type, np.number))
  cPercent = []
  cNoPercent = []
  for ci, c in enumerate(columns):
    if ci >= nbFactorColumns:
      if '%' in c:
        cPercent.append(ci)
      else:
        cNoPercent.append(ci)
  form = '{0:.'+str(experiment._display.metricPrecision-2)+'f}'
  df[df.columns[cPercent]]= df[df.columns[cPercent]].applymap(form.format)
  form = '{0:.'+str(experiment._display.metricPrecision)+'f}'
  df[df.columns[cNoPercent]]= df[df.columns[cNoPercent]].applymap(form.format)

  styler = df.style.set_properties(subset=df.columns[numeric_col_mask], # right-align the numeric columns and set their width
        **{'width':'10em', 'text-align':'right'})\
        .set_properties(subset=df.columns[~numeric_col_mask], # left-align the non-numeric columns and set their width
        **{'width':'10em', 'text-align':'left'})\
        .set_properties(subset=df.columns[nbFactorColumns], # left-align the non-numeric columns and set their width
        **{'border-left':'.1rem solid'})\
        .set_table_styles([d])
  if not experiment._display.showRowIndex:
    styler.hide_index()


  print(header)
  print(df)
  body = '<div> Mask = '+args.mask+'</div>'
  body += '<div> '+header+' </div><br>'+styler.render()
  if args.export != 'none':
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
      columnFormat = ''
      for n in numeric_col_mask:
        if n:
          columnFormat+='r'
        else:
          columnFormat+='l'
      df.to_latex(buf=exportFileName+'.tex', column_format=columnFormat, index=experiment._display.showRowIndex, bold_rows=True)

    if 'png' in args.export or 'all' == args.export:
      subprocess.call(
        'wkhtmltoimage -f png --width 0 '+exportFileName+'.html '+exportFileName+'.png', shell=True)
    if 'pdf' in args.export or 'all' == args.export:
      # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless --print-to-pdf=testChrome.pdf cds.html --print-to-pdf-no-header
      subprocess.call(
      'wkhtmltopdf '+exportFileName+'.html '+exportFileName+'.pdf', shell=True)
      subprocess.call(
      'pdfcrop '+exportFileName+'.pdf '+exportFileName+'.pdf', shell=True)
    if 'html' not in args.export and 'all' != args.export:
      os.remove(exportFileName+'.html')
