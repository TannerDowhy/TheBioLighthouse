#!/usr/bin/python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: This is a module to assist with submitting jobs to the SLURM job scheduler.
description:
    - Longer description of the module.
    - You might include instructions.
version_added: "2.7"
author: "Tanner Dowhy (@TannerDowhy)"
options:
    input_files:
        description:
            - Path to the input FASTQ files to be merged
        required: true
    executable:
        description:
            - The path to the Cutadapt executable. Should be specified but if
              it isn't it will be located.
        required: false
    base_dir:
        description:
            - The path to where the analysis is to take place.
        required: true
        default: Home directory. This needs to be changed if the user doesn't
                 have write access to the home directory or if the environment
                 requires a different path such as in the case of Compute Canada.
    hpc: 
        description: 
            - Boolean variable on whether the run is executed on a regular or HPC machine.
        required: false
        default: false
    slurm_spec: 
        description:
            - The SLURM options if hpc was set to true.
        required: false
        note: Required if hpc was set to true.
notes:
    - This module will make you cool.
'''

EXAMPLES = '''
- name: Execute merge command
  flash2_merge:
    input_files: "{{ base_path }}/.biolighthouse/primer_removal/output"
    base_dir: "{{ base_path }}"
    compress: True
    hpc: False

- name: Execute merge command
  flash2_merge:
    input_files: "{{ base_path }}/.biolighthouse/primer_removal/output"
    base_dir: "{{ base_path }}"
    quality_cutoff: 8
    percent_cutoff: 50
    min_overlap: 15
    fragment_len_stddev: 20
    compress: True
    hpc: True
  slurm_spec:
    account: "{{ account }}"
    time: 5:00
    tasks_per_node: 1
    job_name: biolighthouse
    mem: 2G
'''

RETURN = '''
cmd:
    description: The command that was executed
    type: str
out:
    description: The output message that the module generates
err:
    description: The error message that the modules generates
'''

from ansible.module_utils.basic import AnsibleModule
import imp
import glob
from os.path import expanduser
import os

def flash2_arg_spec(slurm, **kwargs):
    spec = dict(
        input_files=dict(type='path', required=True),
        base_dir=dict(type='path', default=expanduser('~')),
        hpc=dict(type='bool', default=False),
        executable=dict(type='path', default=None, required=False),
        quality_cutoff=dict(type='int', default=2),
        percent_cutoff=dict(type='int', default=50),
        no_discard=dict(type='bool', default=False),
        compress=dict(type='bool', default=False),
        min_overlap=dict(type='int', default=10),
        max_overlap=dict(type='int', default=None),
        min_overlap_outie=dict(type='int', default=35),
        max_mismatch_density=dict(type='float', default=0.25),
        allow_outies=dict(type='bool', default=False),
        phred_offset=dict(type='int', default=33, choices=[33, 64]),
        read_len=dict(type='int', default=100),
        fragment_len=dict(type='int', default=180),
        fragment_len_stddev=dict(type='int', default=18),
        threads=dict(type='int', default=1),
        slurm_spec=dict(type='dict', default=slurm.slurm_arg_spec(), required=False)
    )
    spec.update(kwargs)
    return spec

def run_flash2(fi, executable, merge_path, module):
    f = fi.split('/')
    f = f[-1]
    f = f.replace('.fastq.gz', '')
    b = f.replace('_R1', '')
    file_r = fi.replace('_R1', '_R2')
    f_r = f.replace('_R1', '_R2')
    cmd = get_common_spec(module, executable)
    cmd.extend([fi, file_r, '-o', 'output/%s' % f, '>', 'reports/%s.report' % f])
    with open('%s/merge.sh' % (merge_path), 'a+') as f:
        f.write('%s\n' % (' '.join(cmd)))
        f.close()
    return cmd

def get_common_spec(module, executable):
    cmd = [executable]
    if module.params['quality_cutoff'] != 2:
        cmd.extend(['-Q', str(module.params['quality_cutoff'])])
    if module.params['percent_cutoff'] != 50:
        cmd.extend(['-C', str(module.params['percent_cutoff'])])
    if module.params['no_discard']:
        cmd.extend(['--no-discard'])
    if module.params['min_overlap'] != 10:
        cmd.extend(['-m', str(module.params['min_overlap'])])
    if module.params['max_overlap'] is not None:
        cmd.extend(['-M', str(module.params['max_overlap'])])
    if module.params['min_overlap_outie'] != 35:
        cmd.extend(['-e', str(module.params['min_overlap_outie'])])
    if module.params['max_mismatch_density'] != 0.25:
        cmd.extend(['-X', str(module.params['max_mismatch_density'])])
    if module.params['allow_outies']:
        cmd.extend(['--allow-outies'])
    if module.params['phred_offset'] == 64:
        cmd.extend(['-p 64'])
    if module.params['compress'] == True:
        cmd.extend(['-z'])
    if module.params['phred_offset'] == 33:
        cmd.extend(['-p 33'])
    if module.params['read_len'] != 100:
        cmd.extend(['-r', str(module.params['read_len'])])
    if module.params['fragment_len'] != 180:
        cmd.extend(['-f', str(module.params['fragment_len'])])
    if module.params['fragment_len_stddev'] != 18:
        cmd.extend(['-s', str(module.params['fragment_len_stddev'])])
    # if module.params['threads'] != 1:
    cmd.extend(['-t', str(module.params['threads'])])
    return cmd

def main():
    slurm = imp.load_source('utils.slurm', '/tmp/biol/slurm.py')
    tool = imp.load_source('utils.tool', '/tmp/biol/tool.py')
    argument_spec=flash2_arg_spec(slurm)
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True
                           )
    result = dict(
        changed=False,
        rc = '',
        out= '',
        err='',
        cmd=''
    )
    flash2 = tool.Tool(module.params['base_dir'], 'flash2')
    executable = flash2.get_executable_path(module)

    if module.check_mode:
        return result

    merge_path = "%s/.biolighthouse/merge" % module.params['base_dir']

    # if module.params['slurm_spec']['account'] is not None:
    if module.params['hpc']:
        slurm_cmd = slurm.build_slurm_cmd(module)
    with open('%s/merge.sh' % (merge_path), 'w') as f:
        f.write('%s\n\n' % ('#!/bin/bash'))
        f.close()
    import subprocess
    subprocess.call(['chmod', '0777', '%s/merge.sh' % merge_path])
    for file in glob.glob("%s/*_R1*" % (module.params['input_files'])):
        cmd = run_flash2(file, executable, merge_path, module)

    # if module.params['slurm_spec']['account'] is not None:
    if module.params['hpc']:
        cmd_2 = slurm_cmd
        cmd_2.append('%s/merge.sh' % merge_path)
    else:
        cmd_2 = ['./merge.sh']
    rc, out, err = module.run_command(cmd_2, cwd=merge_path)
    result['rc'] = '%s' % (rc)
    result['err'] += '%s' % (err)
    result['changed'] = True
    result['cmd'] = cmd_2
    module.exit_json(**result)

if __name__ == '__main__':
    main()
