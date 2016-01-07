
aa = """
open cart
close cart
initiate empty cart
confirm empty cart
cancel empty cart
proceed to checkout success
proceed to checkout fail
select shipping method success
select shipping method fail
review cart success
review cart fail
initiate order placement
confirm order placement
cancel order placement
open messages
close messages
send message success
send message fail
open seller drawer
close seller drawer
use saved address for shipping
use saved address for billing
"""

aa = """
open share dialog
close share dialog
focus share link
focus share embed code
"""

aa = """
open catalog
close catalog
open catalog drawer
close catalog drawer
load more catalog images
"""

import inflection
import json

for line in aa.splitlines():
    if line:
        print(inflection.camelize(line.replace(' ', '_'), False) + ': ' + json.dumps(line) + ',')