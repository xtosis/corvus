import pandas as pd
from corvus import (generateCorvus, drawLine, searchCorvus, showReport,
                    exportErrors)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 10000)
pd.set_option('display.max_colwidth', -1)
pd.set_option('display.colheader_justify', 'left')

# inputs
ROOT = '../sovereign'
VERBOSE = 0
FIX = {'.codeclimate.yml': '.yml',
       '.i18n.json': '.json',
       '.resize.js': '.js',
       '.test.js': '.js',
       '.tests.js': '.js',
       '.ui.touch-punch.min.js': '.js'}
DROP_EXT = ['.md',
            '.gitignore',
            '.meteorignore',
            '.yaml',
            '.id',
            '.pack',
            '.idx',
            '.finished-upgraders',
            '.env',
            '.sh',
            '.yml',
            '.sample']
DESCRIPTION = {-1: 'file too short',
               0: 'zero length',
               1: 'new type of syntax',
               2: 'no ending } found in file',
               3: '; found in function text',
               4: 'no \' from \' found after \'import {\'',
               5: 'no qoutes found after \' from \'',
               6: 'illegal characters in directory',
               7: 'unknown case',
               8: 'no ending quote for directory text',
               9: 'possible typo or file does not exist',
               10: 'WARNING: duplicate entries attempted'}

# generating main corvus dataframe
df = generateCorvus(ROOT, FIX, DROP_EXT, VERBOSE)

# find calls, dependencies and functions of each directory in corvus dataframe
df, dirs, errorLog, report = searchCorvus(ROOT, df, 18)
print 'C0RVUS| finished search'
drawLine()

# print search report
STATS = showReport(df, dirs, errorLog, report, DESCRIPTION,
                   PARTS=[False, True, True])

print 'C0RVUS| files with dependencies only:'
temp = STATS['only_dep'].iloc[:, :2].sort_values(['EXT', 'DIR'])
for i in temp.index:
    print '   {:03}| {} {}'.format(i,
                                   temp.loc[i, 'EXT'],
                                   temp.loc[i, 'DIR'])
drawLine()

if False:
    print 'C0RVUS| files with no dependencies and no calls:'
    print STATS['neither'].iloc[:, :2].sort_values(['EXT', 'DIR'])
    drawLine()

# exporting errors
exportErrors(ROOT, dirs, errorLog, DESCRIPTION)
print 'C0RVUS| exported error logs'
drawLine()
