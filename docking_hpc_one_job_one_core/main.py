from run import main_docking
import os
import glob
def write_run(lig_filename,glide_grid_filename,max_conf_num,core_id,run_filename):
    x = [f'''#!/bin/bash

#BATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH -p parallel
#SBATCH --cpus-per-task=1
#SBATCH --mem=50GB
#SBATCH --time=120:00:00
#SBATCH --job-name=C{core_id}
#SBATCH --mail-user=zhangyq9697@gmail.com
#SBATCH --output=slurm_%j_l2_dropout.out


source ~/bash_scratch_conda
conda activate aidrug2020

python -u run.py {lig_filename} {glide_grid_filename} {max_conf_num} {core_id} >out{core_id}.log''']
    with open(run_filename,'w') as f:
        for s in x:
            f.write(s)
    return
if __name__ == '__main__':
    lig_filename = './total_mol.smi'
    glide_grid_filename = './glide-grid_4.zip'
    max_conf_num = 5
    core_mol_num = 10000



    os.system(f'mkdir lig_dataset')
    os.system(f'split -d -l {core_mol_num} {lig_filename} ./lig_dataset/split.smi.')
    all_split_filename = list(glob.glob(r'./lig_dataset/split*'))
    for filename in all_split_filename:
        rf = filename.split('.')[-1]
        os.system(f'mv {filename} ./lig_dataset/{rf}_split.smi')
    all_lig_filename = list(glob.glob(r'./lig_dataset/*.smi*'))
    for core_id,lig_filename in enumerate(all_lig_filename):
        run_filename = f'srun_{core_id}.s'
        write_run(lig_filename,glide_grid_filename,max_conf_num,core_id,run_filename)
        os.system(f'sbatch {run_filename}')
        os.system(f'rm {run_filename}')


