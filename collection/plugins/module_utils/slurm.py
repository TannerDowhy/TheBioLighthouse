#!/usr/bin/python

# Copyright: (c) 2019, Tanner Dowhy <tanner.dowhy@usask.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt
from os.path import expanduser

def slurm_arg_spec():
    return dict(
        account=dict(type='str', default=None, required=False),
        job_name=dict(type='str', default=None, required=False),
        num_nodes=dict(type='int', default=1, required=False),
        time=dict(type='str', default=None, required=False),
        mem=dict(type='str', defualt=None, required=False),
        tasks_per_node=dict(type='int', default=None, required=False),
        # array=dict(type='str', default=None, required=False),
        cmd=dict(type='str', default=None, required=False)
    )

def build_slurm_cmd(module):
    cmd = ['sbatch', '--dependency=singleton', '--nodes=%s' % module.params['slurm_spec']['num_nodes'],'--account=%s' % module.params['slurm_spec']['account'], '--time=%s' % module.params['slurm_spec']['time']]
    # if module.params['slurm_spec']['array'] is not None:
    #     cmd += " --array=%s" % (module.params['slurm_spec']['array'])
    if module.params['slurm_spec']['job_name'] is not None:
        cmd.extend(['--job-name=%s' % module.params['slurm_spec']['job_name']])
    # if module.params['slurm_spec']['num_nodes'] is not None:
    #     cmd += " --nodes=%s" % (module.params['slurm_spec']['num_nodes'])
    if module.params['slurm_spec']['mem'] is not None:
        cmd.extend(['--mem=%s' % module.params['slurm_spec']['mem']])
    if module.params['slurm_spec']['tasks_per_node'] is not None:
        cmd.extend(['--tasks-per-node=%s' % module.params['slurm_spec']['tasks_per_node']])
    return cmd
