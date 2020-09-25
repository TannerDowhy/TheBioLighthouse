#!/usr/bin/python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: This is a module to execute the DADA2 Sample Inference step.
version_added: "2.7"
author: "Tanner Dowhy (@TannerDowhy)"
options:
    name:
        reads:
            - This is the path to the input FASTQ reads
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
    extension:
        description:
            - A file wildcard that matches the end of the file.
        required: false
        default: .extendedFrags.fastq
    trunc_len:
        description:
            - Truncation length for reads. Should not be set for most use cases.
        required: false
        default: 0
    nbases:
        description:
            - The number of bases to use in learning sequencing errors with DADA2.
        required: false
        default: 1000000
    output:
        description:
            - The name of the output ASV tables.
        required: true
    random_seed:
        description:
            - The random seed used for learning sequencing errors with DADA2.
        required: false
        default: 0
    max_consist:
        description:
            - The maximum number of steps used by DADA2 for convergence of learning 
              sequencing errors.
        required: false
        default: 10
    slurm_spec: 
        description:
            - The SLURM options if hpc was set to true.
        required: false
        note: Required if hpc was set to true.
notes:
    - DADA2 must be installed.
'''

EXAMPLES = '''
- name: Run DADA2 Sample Inference
  dada2_sample_inference:
    reads: "{{ base_path }}/.biolighthouse/merge/output"
    base_dir: "{{ base_path }}"
    output: seqtab
    hpc: False

- name: Run DADA2 Sample Inference
  dada2_sample_inference:
    reads: "{{ base_path }}/.biolighthouse/merge/output"
    base_dir: "{{ base_path }}"
    executable: "{{ base_path }}/.biolighthouse/software/conda/envs/dada2/bin/Rscript"
    output: seqtab
    hpc: True
    slurm_spec:
      account: "{{ account }}"
      job_name: "biolighthouse"
      mem: 48G
      time: 48:00
      tasks_per_node: 48
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
import glob
import subprocess
import imp
# import importlib
from os.path import expanduser

def dada2_sample_inference_arg_spec(slurm, **kwargs):
    spec = dict(
        reads=dict(type='path', default=None, required=True),
        hpc=dict(type='bool', default=False),
        executable=dict(type='path', default=None, required=False),
        base_dir=dict(type='path', default=None, required=False),
        extension=dict(type='str', default='.extendedFrags.fastq'),
        trunc_len=dict(type='int', default=0, required=False),
        nbases=dict(type='int', default=1000000, required=False),
        output=dict(type='str', required=True),
        random_seed=dict(type='int', default=0),
        max_consist=dict(type='int', default=10),
        slurm_spec=dict(type='dict', default=slurm.slurm_arg_spec(), required=False)
    )
    spec.update(kwargs)
    return spec

def build_sample_inference_command(module, dada2_path, executable):
    cmd = [executable, '%s/sample_inference.R' % dada2_path, '%s/.biolighthouse/conda/envs/biolighthouse/lib/R/library' % module.params['base_dir'],
        module.params['reads'], ".extended", str(module.params['trunc_len']), ".extended", str(module.params['random_seed']),
        str(module.params['nbases']), str(module.params['max_consist']), '%s/%s.csv' % (dada2_path, module.params['output']),
        '%s/%s.rds' % (dada2_path, module.params['output'])]
    return cmd

def main():
    tool = imp.load_source('utils.tool', '/tmp/biol/tool.py')
    slurm = imp.load_source('utils.slurm', '/tmp/biol/slurm.py')
    argument_spec=dada2_sample_inference_arg_spec(slurm)
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
    dada2 = tool.Tool(module.params['base_dir'], 'rscript')
    executable = dada2.get_executable_path(module)

    if module.check_mode:
        return result

    dada2_path = "%s/.biolighthouse/DADA2" % module.params['base_dir']

    cmd = build_sample_inference_command(module, dada2_path, executable)
    # print(cmd)
    with open('%s/dada2_sample_inference.sh' % (dada2_path), 'w') as f:
        f.write('%s\n\n%s' % ('#!/bin/bash', ' '.join(cmd)))
        f.close()

    # if module.params['slurm_spec']['account'] is not None:
    if module.params['hpc']:
        slurm_cmd = slurm.build_slurm_cmd(module)
        cmd_2 = slurm_cmd
        cmd_2.extend(['--output=%s/dada2_sample_inference.report' % dada2_path, '%s/dada2_sample_inference.sh' % dada2_path])
        # rc, out, err = module.run_command(cmd_2, cwd=dada2_path)
    else:
        cmd_2 = ['./dada2_sample_inference.sh']
        # rc, out, err = module.run_command(cmd, cwd=dada2_path)
    import subprocess
    subprocess.call(['chmod', '0700', '%s/dada2_sample_inference.sh' % dada2_path])
    rc, out, err = module.run_command(cmd_2, cwd=dada2_path)
    result['changed'] = True
    # result['out'] = out
    result['err'] = err
    result['rc'] = rc
    # result['cmd'] = cmd_2

    module.exit_json(**result)

if __name__ == '__main__':
    main()
