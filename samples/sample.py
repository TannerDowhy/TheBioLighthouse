

def flash2_arg_spec(slurm, **kwargs):
    spec = dict(
        input_files=dict(type='path', required=True),
        base_dir=dict(type='path', default=expanduser('~')),
        hpc=dict(type='bool', default=False),
        executable=dict(type='path', default=None, required=False),
        """ Definition of all tool parameters """ 
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
