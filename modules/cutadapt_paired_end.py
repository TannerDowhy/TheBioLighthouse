#!/usr/bin/python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: This is an Ansible module to execute Cutadapt in paired-end mode.
description:
    - This module generates primer permutations for removal and additionally
      removes adapters. Runs can be executed on bare metal machines as well as
      on a SLURM cluster.
version_added: "2.7"
author: "Tanner Dowhy (@TannerDowhy)"
options:
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
    input_files:
        description:
            - The path to the directory containing the input files.
        required: true
    hpc: 
        description: 
            - Boolean variable on whether the run is executed on a regular or HPC machine.
        required: false
        default: false
    primer: 
        description: 
            - The DNA sequence of the forward primer.
        required: true
    primer_r: 
        description:
            - The DNA sequence of the reverse primer.
        required: true
    pypath:
        description:
            - The path to the python library:
        required: false
    slurm_spec: 
        description:
            - The SLURM options if hpc was set to true.
        required: false
        note: Required if hpc was set to true.
notes:
    - Cutadapt must be installed.
'''

EXAMPLES = '''
- name: Execute cutadapt command
  cutadapt_paired_end:
    input_files: "{{ input_data }}"
    base_dir: "{{ base_path }}"
    primer: CTACGGGGGGCAGCAG
    primer_r: GGACTACCGGGGTATCT
    hpc: False

- name: Execute cutadapt on HPC
  cutadapt_paired_end:
    input_files: "{{ input_data }}"
    base_dir: "{{ base_path }}"
    primer: CTACGGGGGGCAGCAG
    primer_r: GGACTACCGGGGTATCT
    hpc: True
    slurm_spec:
      account: "{{ account_name }}"
      time: '5:00'
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
import os
from os.path import expanduser
from Bio.SeqIO.FastaIO import SimpleFastaParser
from Bio.Seq import Seq

def cutadapt_arg_spec(slurm, **kwargs):
    spec = dict(
        executable=dict(type='path', default=None, required=False),
        hpc=dict(type='bool', default=False),
        pypath=dict(type='path', required=False),
        base_dir=dict(type='path', default=expanduser('~')),
        input_files=dict(type='path', default=None, required=True),
        primer=dict(type='str', default=None, required=False),
        primer_r=dict(type='str', default=None, required=False),
        front=dict(type='str', default=None, required=False),
        anywhere=dict(type='str', default=None, required=False),
        error_rate=dict(type='float', default=0.1),
        no_indels=dict(type='bool', default=False, required=False),
        count=dict(type='int', default=1, required=False),
        overlap=dict(type='int', default=3, required=False),
        cores=dict(type='int', default=1),
        match_read_wildcards=dict(type='bool', default=False, required=False),
        no_match_adapter_wildcards=dict(type='bool', default=False, required=False),
        action=dict(type='str', default='trim', choices=['trim', 'mask', 'none']),
        length=dict(type='list', default=None, required=False),
        nextseq_trim=dict(type='str', default=None, required=False),
        quality_cutoff=dict(type='list', default=None, required=False),
        quality_base=dict(type='str', default='33', required=False),
        read_length=dict(type='int', default=None, required=False),
        trim_n=dict(type='bool', default=False, required=False),
        length_tag=dict(type='str', default=None, required=False),
        strip_suffix=dict(type='str', default=None, required=False),
        prefix=dict(type='str', default=None, required=False),
        suffix=dict(type='str', default=None, required=False),
        minimum_length=dict(type='int', default=0, required=False),
        maximum_length=dict(type='int', default=None, required=False),
        max_n=dict(type='float', default=None, required=False),
        discard_trimmed=dict(type='bool', default=False, required=False),
        discard_untrimmed=dict(type='bool', default=False, required=False),
        discard_casava=dict(type='bool', default=False, required=False),
        report=dict(type='str', default='full', required=False),
        wildcard_file=dict(type='path', default=None, required=False),
        # TODO: fix these three output to booleans
        too_short_output=dict(type='path', default=None, required=False),
        too_long_output=dict(type='path', default=None, required=False),
        untrimmed_output=dict(type='path', default=None, required=False),
        colorspace=dict(type='bool', default=False, required=False),
        double_encode=dict(type='bool', default=False, required=False),
        trim_primer=dict(type='bool', default=False, required=False),
        strip_f3=dict(type='bool', default=False, required=False),
        maq=dict(type='bool', default=False, required=False),
        bwa=dict(type='bool', default=False, required=False),
        zero_cap=dict(type='bool', default=False, required=False),
        no_zero_cap=dict(type='bool', default=False, required=False),
        front_r=dict(type='str', default=None, required=False),
        anywhere_r=dict(type='str', default=None, required=False),
        length_r=dict(type='int', default=None, required=False),
        pair_filter=dict(type='str', default='any', choices=['any', 'both', 'first']),
        interleaved=dict(type='bool', default=False, required=False),
        # TODO: change these three outputs to booleans
        untrimmed_paired_output=dict(type='path', default=None, required=False),
        too_short_paired_output=dict(type='path', default=None, required=False),
        too_long_paired_output=dict(type='path', default=None, required=False),
        slurm_spec=dict(type='dict', default=slurm.slurm_arg_spec(), required=False)
    )
    spec.update(kwargs)
    return spec

def write_fasta(f_path, forward, reverse):
    with open('%s/primers.fa' % (f_path), 'w') as f: # fix path
        f.write('>forward/f')
        f.write('\n')
        f.write(forward)
        f.write('\n')
        f.write('>reverse/r')
        f.write('\n')
        f.write(reverse)
        f.close()

def run_cutadapt(fi, perms, executable, cut_path, module):
    f = fi.split('/')
    f = f[-1]
    f = f.replace('.fastq.gz', '')
    b = f.replace('_R1', '')
    file_r = fi.replace('_R1', '_R2')
    f_r = f.replace('_R1', '_R2')
    cmd = get_common_spec(module, executable)
    cmd = build_primer_pe_cmd(perms, cmd)
    cmd.extend([fi, file_r, '-o', '%s/output/%s.fastq.gz' % (cut_path, f), '-p', '%s/output/%s.fastq.gz' % (cut_path, f_r), '>', '%s/reports/%s.report' % (cut_path, b)])
    with open('%s/primer_removal.sh' % (cut_path), 'a+') as f:
        f.write('%s\n' % (' '.join(cmd)))
        f.close()
    return cmd

def build_primer_pe_cmd(primers, cmd):
    cmd.extend([primers[0][2], '%s=%s' % (primers[0][0], primers[0][1]), primers[1][2], '%s=%s' % (primers[1][0],primers[1][1]),
        primers[2][2], '%s=%s' % (primers[2][0],primers[2][1]), primers[3][2],
        '%s=%s' % (primers[3][0],primers[3][1])])
    return cmd

def get_common_spec(module, executable):
    cmd = [executable, '-n', str(module.params['count']), '--pair-filter=%s' % module.params['pair_filter'], '--quality-base=%s' % module.params['quality_base'], '-m', str(module.params['minimum_length'])]
    # if module.params['cores'] != 1:
    cmd.extend(['-j', str(module.params['cores'])])
    if module.params['overlap'] != 3:
        cmd.extend(['-O', str(module.params['overlap'])])
    if module.params['report'] != 'full':
        cmd.extend(['--report=%s' % module.params['report']])
    if module.params['action'] != 'trim':
        cmd.extend(['--action=%s' % module.params['action']])
    if module.params['error_rate'] != 0.1:
        cmd.extend(['-e', str(module.params['error_rate'])])
    if module.params['maximum_length'] is not None:
        cmd.extend(['-M', str(module.params['maximum_length'])])
    if module.params['no_indels']:
        cmd.extend(['--no-indels'])
    if module.params['match_read_wildcards']:
        cmd.extend(['--match-read-wildcards'])
    if module.params['no_match_adapter_wildcards']:
        cmd.extend(['--no-match-adapter-wildcards'])
    if module.params['discard_trimmed']:
        cmd.extend(['--discard-trimmed'])
    if module.params['discard_untrimmed']:
        cmd.extend(['--discard-untrimmed'])
    if module.params['suffix'] is not None:
        cmd.extend(['-y', str(module.params['suffix'])])
    if module.params['discard_casava']:
        cmd.extend(['--discard-casava'])
    if module.params['trim_n']:
        cmd.extend(['--trim-n'])
    if module.params['max_n'] is not None:
        cmd.extend(['--max-n', str(module.params['max_n'])])
    return cmd

def gen_permutations_pe(fasta):
    primers = []
    primers_rc = []
    primers_tmp = []

    with open(fasta) as f:
        for t in SimpleFastaParser(f):
            a = t[0].split('/')
            primers_tmp.append([a[0], a[1], t[1]])
    f.close()

    for a in primers_tmp:
        primers_rc.append([a[0], a[1], a[2]])
        primers_rc.append([a[0]+str("_rc"), a[1]+str('_rc'), str(Seq(a[2]).reverse_complement())])

    one = primers_rc[0]
    one_rc = primers_rc[1]
    two = primers_rc[2]
    two_rc = primers_rc[3]

    for a in range(4):
        if a == 0:
            primers.append([one[0], one[2], " -g", one[1]])
        elif a == 1:
            primers.append([one_rc[0], one_rc[2], "-A", one_rc[1]])
        elif a == 2:
            primers.append([two[0], two[2], "-G", two[1]])
        elif a == 3:
            primers.append([two_rc[0], two_rc[2], "-a", two_rc[1]])
        else:
            print("Something's gone horribly wrong. Have fun debugging.")
    return primers

def main():
    slurm = imp.load_source('utils.slurm', '/tmp/biol/slurm.py')
    tool = imp.load_source('utils.tool', '/tmp/biol/tool.py')
    argument_spec=cutadapt_arg_spec(slurm)
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
    # Define the variables
    cutadapt = tool.Tool(module.params['base_dir'], 'cutadapt')
    executable = cutadapt.get_executable_path(module)

    if module.check_mode:
        return result

    cut_path = "%s/.biolighthouse/primer_removal" % module.params['base_dir']

    # if module.params['slurm_spec']['account'] is not None:
    if module.params['hpc']:
        slurm_cmd = slurm.build_slurm_cmd(module)
    with open('%s/primer_removal.sh' % (cut_path), 'w') as f:
        f.write('%s\n\n' % ('#!/bin/bash'))
        f.close()
    import subprocess
    subprocess.call(['chmod', '0777', '%s/primer_removal.sh' % cut_path])
    write_fasta(cut_path, module.params['primer'], module.params['primer_r'])
    perms = gen_permutations_pe("%s/primers.fa" % cut_path)
    for fi in glob.glob('%s/*_R1*' % (module.params['input_files'])):
        cmd = run_cutadapt(fi, perms, executable, cut_path, module)
    # if module.params['slurm_spec']['account'] is not None:
    if module.params['hpc']:
        cmd_2 = slurm_cmd
        cmd_2.append('%s/primer_removal.sh' % cut_path)
    else:
        cmd_2 = ['./primer_removal.sh']
    result['cmd'] = cmd_2
    rc, out, err = module.run_command(cmd_2, cwd=cut_path)
    result['changed'] = True
    result['out'] = out
    result['err'] = err
    result['rc'] = rc
    module.exit_json(**result)

if __name__ == '__main__':
    main()
