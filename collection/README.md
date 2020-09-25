#The BioLighthouse

The BioLighthouse uses [Ansible](https://github.com/ansible/ansible/ "Ansible") to configure and execute bioinformatics workflows. The BioLighthouse leverages Conda environments to configure pipelines in user-space and 
automates execution on could, shared, and high-performance computing
machines. 

##Design Principles
###From [Ansible](https://github.com/ansible/ansible/blob/devel/README.rst"Ansible README"):
*  Have a dead simple setup process and a minimal learning curve.
*  Manage machines very quickly and in parallel.
*  Avoid custom-agents and additional open ports, be agentless by
   leveraging the existing SSH daemon.
*  Describe infrastructure in a language that is both machine and human
   friendly.
*  Focus on security and easy auditability/review/rewriting of content.
*  Manage new remote machines instantly, without bootstrapping any
   software.
*  Allow module development in any dynamic language, not just Python.
*  Be usable as non-root.
*  Be the easiest IT automation system to use, ever.

###The BioLighthouse:
*  Simple setup and use regardless of computational skill/knowledge.
*  Configure and execute pipelines on a variety of machines.
*  Describe infrastructure and pipelines in a language that is both .
*  Machine and human readable. 
*  Configure and execute pipelines as non-root in Conda environments.

###Use The BioLighthouse
Install [Ansible](https://github.com/ansible/ansible/ "Ansible"):
```
pip install ansible
```

Get collection from [Ansible Galaxy](https://galaxy.ansible.com/coadunate/thebiolighthouse "The BioLighthouse"):
```
ansible-galaxy collection install coadunate.thebiolighthouse
```

Add ```ANSIBLE_LIBRARY={{ path_to_modules }}``` in ```~/.ansible.cfg```
file.

### Creating Configuration Roles
Configuration roles configure a single tool within a Conda environment. 
All tools are thus dependent on the Conda configuration role and module. 
Each tool is contained in its own Conda environment to avoid dependency
collisions. Use the ansible-role-blConfigSetup as a template to start a
configuration role. 

###Developing Modules
The boiler-plate code provided by Ansible for developing modules can be 
found [here].(https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#starting-a-new-module "Starting a new module") The argument specification is a Python dictionary containing all of the parameters possible for invocation of a tool as well as any user-defined parameters to make execution more clear. Some user-defined variables that may be useful include the location of the executable, the base directory where the analysis is to be written, and a boolean specifying whether the tool is to be executed on an HPC machine. If the tool can be run on an HPC machine, a SLURM spec argument is defined and inherits from the SLURM utility object. 

In the main function, the logic is built in order to set up the command for executing a tool based on the parameters provided. If the tool is to be run on HPC infrastructure, the code is to build a SLURM (or other manager) script and submit it on the CLI. Return values are stored in a dictionary and returned after the run.  


###Creating Pipelines 
Execution pipelines are built within Ansible roles. In the tasks file, setup the environment as in creating configuration roles then build the pipeline using the modules built for each tool. For each tool, it is required to activate the conda environment before the module is used and to deactivate the environment after the module is used. In the meta file, specify each tool's configuration role as a dependency so they will be configured automatically.

