#!/usr/bin/python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

import os

class Tool(object):
    def __init__(self, base_dir, exe_name):
        self.exe_name = exe_name
        self.base_dir = base_dir

    def get_executable_path(self, module):
        if module.params['executable']:
            if os.path.isfile(module.params['executable']):
                return module.params['executable']
            else:
                module.fail_json(msg = "%s is not a valid executable."
                    % (module.params['executable']))
        else:
            executable = module.get_bin_path(self.exe_name)
            if not executable:
                module.fail_json(msg = '%s not found in PATH and executable is not specified.'
                    % (self.exe_name))
        return executable
