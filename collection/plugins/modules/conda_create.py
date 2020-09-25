#!/usr/bin/env python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: Create conda environment.
version_added: "2.7"
author: "Tanner Dowhy (@TannerDowhy)"
options:
    name:
        description:
            - The name of the environment to create
        required: true
    env_path:
        description:
            - The path to the environment to create
        required: false
    file:
        description:
            - Read package versions from a given file
        required: false
    channel:
        description:
            - Additional channels to search for packages
        required: false
    executable:
        description:
            - Path to the conda executable
        required: false
    pyv:
        description:
            - Version of python for the Conda environment/
        required: false
    packages:
        description:
            - The names of any packages to be installed during creation
        required: false
notes:
    - Conda must be installed first. The environment must not currently exist.
'''

EXAMPLES = '''
- name: Create simple conda environment
  conda_create:
    name: my_env

- name: Create conda environment with executable
  conda_create:
    name: my_env
    executable: "{{ ansible_env.HOME }}"/env

- name: Create conda environment with executable and package
  conda_create:
    name: my_env
    executable: "{{ ansible_env.HOME }}"/env
    packages: scipy
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import imp

def conda_create_arg_spec(**kwargs):
    spec = dict(
        # clone=dict(type='path', default=None, required=False),
        file=dict(type='list', default=None, required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', default=None, requred=True),
        env_path=dict(type='path', default=None, required=False),
        pyv=dict(type="str", required=False, default="2.7"),
        channel=dict(type='list', defualt=[], required=False),
        executable=dict(type='path', required=False),
        packages=dict(type='list', default=None, required=False)
    )
    spec.update(kwargs)
    return spec

def main():
    conda = imp.load_source('utils.conda', '/tmp/biol/conda.py')
    argument_spec=conda_create_arg_spec()

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True
                           )

    result = dict(
        changed=False
    )

    name = module.params['name']
    state = module.params['state']
    file = module.params['file']
    env_path = module.params['env_path']
    channel = module.params['channel']
    executable = module.params['executable']
    pyv = module.params['pyv']

    # Create conda object
    conda = conda.Conda(module, name)

    if module.check_mode:
        return result

    name_exists = conda.check_env(name)
    if not name_exists:
        if state == 'absent':
            result['msg'] = "%s is already absent." % (name)
            module.exit_json(**result)
        else:
            conda.create_env(name)
            result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
