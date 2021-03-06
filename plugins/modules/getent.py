#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Brian Coca <brian.coca+dev@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: getent
short_description: A wrapper to the unix getent utility
description:
     - Runs getent against one of it's various databases and returns information for the host, use 'register' to capture for reuse.
options:
    database:
        description:
            - The name of a getent database supported by the target system (passwd, group,
              hosts, etc).
        required: True
    key:
        description:
            - Key from which to return values from the specified database, otherwise the
              full contents are returned.
        default: ''
    split:
        description:
            - "Character used to split the database values into lists/arrays such as ':' or '\t', otherwise  it will try to pick one depending on the database."
    fail_key:
        description:
            - If a supplied key is missing this will make the task fail if C(yes).
        type: bool
        default: 'yes'

notes:
   - Not all databases support enumeration, check system documentation for details.
author:
- Brian Coca (@bcoca)
'''

EXAMPLES = '''
# get root user info
- getent:
    database: passwd
    key: root
  register: getent_password
- debug:
    var: getent_passwd

# get all groups
- getent:
    database: group
    split: ':'
  register: getent_group
- debug:
    var: getent_group

# get all hosts, split by tab
- getent:
    database: hosts
  register: getent_hosts
- debug:
    var: getent_hosts

# get http service info, no error if missing
- getent:
    database: services
    key: http
    fail_key: False
  register: getnent_services
- debug:
    var: getent_services

# get user password hash (requires sudo/root)
- getent:
    database: shadow
    key: www-data
    split: ':'
  register: getnent_shadow
- debug:
    var: getent_shadow

'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

module = AnsibleModule(
    argument_spec=dict(
        database=dict(type='str', required=True),
        key=dict(type='str'),
        split=dict(type='str'),
        fail_key=dict(type='bool', default=True),
    ),
    supports_check_mode=True,
)

colon = ['passwd', 'shadow', 'group', 'gshadow']

database = module.params['database']
key = module.params.get('key')
split = module.params.get('split')
fail_key = module.params.get('fail_key')

getent_bin = module.get_bin_path('getent', True)

if key is not None:
    cmd = [getent_bin, database, key]
else:
    cmd = [getent_bin, database]

if split is None and database in colon:
    split = ':'

try:
    rc, out, err = module.run_command(cmd)
except Exception as e:
    module.fail_json(msg=to_native(e), exception=traceback.format_exc())

msg = "Unexpected failure!"
dbtree = 'getent_%s' % database
results = {'collection': True, dbtree: {}}

if rc == 0:
    for line in out.splitlines():
        record = line.split(split)
        results[dbtree][record[0]] = record[1:]

    module.exit_json(**results)

elif rc == 1:
    msg = "Missing arguments, or database unknown."
elif rc == 2:
    msg = "One or more supplied key could not be found in the database."
    if not fail_key:
        results[dbtree][key] = None
        module.exit_json(results=results, msg=msg)
elif rc == 3:
    msg = "Enumeration not supported on this database."

module.fail_json(msg=msg)
