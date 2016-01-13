
aa = """
open catalog share dialog
close catalog share dialog
focus catalog share link
focus catalog share embed code
"""

import inflection
import json

for line in aa.splitlines():
    if line:
        print(inflection.camelize(line.replace(' ', '_'), False) + ': ' + json.dumps(line) + ',')