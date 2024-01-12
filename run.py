import os
from multiprocessing import Pool
import glob,inspect

'''
$SCHRODINGER/ligprep -NJOBS 36 -SUBHOST localhost:36 -epik -ismi zinc_all.smi -omae ligprep_zinc-out.maegz -LOCAL -WAIT
structconvert -imae ligprep_zinc-out.maegz -osd ligprep_zinc-out.sdf
$SCHRODINGER/confgen ligprep_zinc-out.sdf -m 100 -optimize -LOCAL -WAIT -NJOBS 36 -HOST localhost:36 -NOJOBID
$SCHRODINGER/glide -n 36 -HOST localhost:36 glide-dock_SP_1.in -WAIT
$SCHRODINGER/utilities/glide_ensemble_merge glide-dock_SP_1_pv.maegz -m 1
structconvert -imae glide_ensemble_merge-poses.maegz -osd docking_ligand.sdf
structconvert -imae glide_ensemble_merge_receptors.maegz -opdb docking_protein.pdb



'''
def run_work_dir(core_id,lig_filename):
    working_dir = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
    if os.path.exists(f'{working_dir}/sub_{core_id}'):
        os.system(f'rm -rf {working_dir}/sub_{core_id}')
    os.system(f'mkdir {working_dir}/sub_{core_id}')
    sub_lig_filename = f"{working_dir}/sub_{core_id}/{lig_filename.split('/')[-1]}"
    os.system(f'cp {lig_filename} {sub_lig_filename}')
    sub_working_dir = f"{working_dir}/sub_{core_id}"
    return sub_lig_filename,sub_working_dir
def run_ligprep(lig_filename):
    out_filename = lig_filename.replace('.smi','-out.maegz')
    print(lig_filename)
    cl = f'$SCHROD_HOME/ligprep -epik -ismi {lig_filename} -omae {out_filename} -LOCAL -WAIT'
    os.system(cl)
    return out_filename
def run_structconvert(prep_filename):
    out_filename = prep_filename.replace('-out.maegz','-prep_out.sdf')
    cl = f'structconvert {prep_filename} {out_filename}'
    os.system(cl)
    return out_filename
def run_confgen(sdf_filename,max_conf_num,sub_working_dir):
    cl = f'$SCHROD_HOME/confgen {sdf_filename} -m {max_conf_num} -optimize -LOCAL -WAIT -NOJOBID'
    os.system(cl)

    sdf_no_dir_filename = sdf_filename.split('/')[-1].replace('.sdf','-out.maegz')
    working_dir  = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0)))
    clo_filename = working_dir     + f'/{sdf_no_dir_filename}'
    out_filename = sub_working_dir + f'/{sdf_no_dir_filename}'
    os.system(f'mv {clo_filename} {out_filename}')

    return out_filename
def run_docking(conf_filename,glide_grid_filename,working_dir,core_id):

    in_str = [f'''FORCEFIELD   OPLS_2005
GRIDFILE   {glide_grid_filename}
LIGANDFILE   {conf_filename}
PRECISION   SP
NOSORT  FALSE
OUTPUTDIR   {working_dir}
''']

    in_filename = f'{working_dir}/glide-dock_SP_{core_id}.in'
    with open(in_filename,'w') as f:
        for s in in_str:
            f.write(s)

    cl = f'$SCHROD_HOME/glide {working_dir}/glide-dock_SP_{core_id}.in -WAIT'
    os.system(cl)
    os.system(f'mv glide-dock_SP_{core_id}* {working_dir}/')
    return 
def combine_result(core_id,working_dir):
    cl1 = f'$SCHROD_HOME/utilities/glide_ensemble_merge {working_dir}/glide-dock_SP_{core_id}_pv.maegz -m 1'
    cl2 = f'structconvert {working_dir}/glide_ensemble_merge-poses.maegz  {working_dir}/docking_ligand.sdf'
    cl3 = f'structconvert {working_dir}/glide_ensemble_merge_receptors.maegz {working_dir}/docking_protein.pdb'
    os.system(cl1)
    os.system(cl2)
    os.system(cl3)
    return 
def main_docking(args):
    lig_filename,glide_grid_filename,max_conf_num,core_id = args

    sub_lig_filename,sub_working_dir   = run_work_dir(core_id,lig_filename)
    prep_filename                      = run_ligprep(sub_lig_filename)
    sdf_filename                       = run_structconvert(prep_filename)
    conf_filename                      = run_confgen(sdf_filename,max_conf_num,sub_working_dir)

    run_docking(conf_filename,glide_grid_filename,sub_working_dir,core_id)

    #combine_result(core_id,sub_working_dir)
    return 

if __name__ == '__main__':
    lig_filename = './total_mol.smi'
    glide_grid_filename = './glide-grid_4.zip'
    max_conf_num = 5
    core_mol_num = 10000


    os.system(f'mkdir lig_dataset')
    os.system(f'split -d -l {core_mol_num} {lig_filename} ./lig_dataset/split.smi.')

    all_split_filename = list(glob.glob(r'./lig_dataset/split.smi.*'))
    for filename in all_split_filename:
        rf = filename.split('.')[-1]
        os.system(f'mv {filename} ./lig_dataset/{rf}_split.smi')

    p = Pool()
    all_lig_filename = list(glob.glob(r'./lig_dataset/*split*'))
    all_args = [[lig_filename,glide_grid_filename,max_conf_num,core_id] for core_id,lig_filename in enumerate(all_lig_filename)]
#    main_docking(all_args[0])
    p.map(main_docking,all_args)

