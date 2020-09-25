#!/usr/bin/env python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: Install Conda packages.
version_added: "2.7"
author: "Tanner Dowhy (@TannerDowhy)"
options:
    name:
        description:
            - The name of the package to install
        required: true
    version:
        description:
            - The version of the package to install
    env_path:
        description:
            - The path to the environment to create
        required: false
    state:
        description:
            - The state of the package: present, absent, or latest.
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
            - Version of python for the Conda environment
        required: false
    environment:
        description:
            - The name of the Conda environment to install the packages in
        required: false
notes:
    - Conda must be installed.
'''

EXAMPLES = '''
- name: Install a conda package
  conda_install:
    name: scipy
    state: latest
    environment: cutadapt_env

- name: Install a conda package
  conda_install:
    name: cutadapt
    channel: bioconda
    version: 1.17
    environment: cutadapt_env

- name: Remove a conda package
  conda_install:
    name: cutadapt
    state: absent

'''

RETURN = '''
actions:
  description: A list of actions taken by conda that modified packages.
  returned: changed
'''

from ansible.module_utils.basic import AnsibleModule
import imp

def conda_install_arg_spec(**kwargs):
    spec = dict(
        state=dict(type='str', choices=['present', 'absent', 'latest'], default='present'),
        name=dict(type='list', default=[], requred=True),
        version=dict(required=False),
        pyv=dict(type="str", required=False, default="2.7"),
        env_path=dict(type='path', default=None, required=False),
        environment=dict(type='str', default=None, required=False),
        channel=dict(type='list', defualt=None, requred=False),
        executable=dict(type='path', required=False)
    )
    spec.update(kwargs)
    return spec

def main():
    conda = imp.load_source('utils.conda', '/tmp/biol/conda.py')
    argument_spec=conda_install_arg_spec()

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True
                           )

    result = dict(
        changed=False,
        actions = []
    )

    state = module.params['state']
    name = module.params['name']
    version = module.params['version']
    env_path = module.params['env_path']
    environment = module.params['environment']
    channel = module.params['channel']
    executable = module.params['executable']

    conda = conda.Conda(module, environment)

    if environment:
        env_exists = conda.check_env(environment)
        if not env_exists:
            result['msg'] = "%s environment does not exist." % environment

    target_packages = [conda.split_name_version(n, version) for n in name]
    installed_packages = conda.list_packages(environment)

    if state == 'present':
        absent_packages = conda.get_absent_packages(target_packages, installed_packages, check_version=True)
        if absent_packages:
            if not module.check_mode:
                actions = conda.install_packages(absent_packages, channel)
                result['actions'] += actions
            result['changed'] = True
    elif state == 'absent':
        present_packages = conda.get_present_packages(
            target_packages, installed_packages,
            check_version=False)
        if present_packages:
            names = [p['name'] for p in present_packages]
            if not module.check_mode:
                actions = conda.remove_packages(names, channel)
                result['actions'] += actions
            result['changed'] = True
    elif state == 'latest':
        # Find missing packages first
        absent_packages = conda.get_absent_packages(target_packages,
                                                    installed_packages,
                                                    check_version=False)
        present_packages = conda.get_present_packages(target_packages,
                                                      installed_packages,
                                                      check_version=False)
        if absent_packages:
            if not module.check_mode:
                actions = conda.install_packages(absent_packages, channel)
                result['actions'] += actions
            result['changed'] = True

        if present_packages:
            # Check what needs to be updated with a dry run
            names = [p['name'] for p in present_packages]
            dry_actions = conda.update_packages(names, channel, dry_run=True)
            if dry_actions:
                if not module.check_mode:
                    actions = conda.update_packages(names, channel)
                    result['actions'] += actions
                result['changed'] = True


    if module.check_mode:
        return result


    module.exit_json(**result)


if __name__ == '__main__':
    main()
