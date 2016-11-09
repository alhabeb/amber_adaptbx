import os
import parmed as pmd
import subprocess
import pytest
from numpy.testing import assert_almost_equal as aa_eq
from amber_adaptbx.tests.utils import (get_fn, tempfolder,
        get_prmtop_and_rst7_and_pdb_filenames_from_pdb,
        get_minimized_pdb_filename,
        get_minimized_rst7_filename,
)
from amber_adaptbx.tests import utils

@pytest.mark.parametrize('pdb_file, LES, minimization_type, expected_rmsd', [
    # 2igd, LES=False/True, minimization_type=amber_all/amber_h
    (get_fn('2igd/2igd.pdb'), False,'amber_h', 0.1171),
    (get_fn('2igd/2igd.pdb'), False,'amber_all', 0.1287),
    (get_fn('2igd/2igd.pdb'), True, 'amber_all', 0.1264),
    (get_fn('2igd/2igd.pdb'), True, 'amber_h', 0.1155),
    # 4lzt, LES=False/True, minimization_type=amber_h
    (get_fn('4lzt/4lzt_no_BHOH.pdb'), False,'amber_h', 0.1043),
    (get_fn('4lzt/4lzt_no_BHOH.pdb'), True,'amber_h', 0.1038),
])
def test_minimization_with_amber_h_LES(pdb_file, LES, minimization_type, expected_rmsd):
  command_build = [
          'phenix.AmberPrep',
          pdb_file,
          'LES={}'.format(LES),
          'minimise={}'.format(minimization_type),
          'minimization_options="maxcyc=100"',
  ]
  prmtop_file, original_rst7_file, _ = get_prmtop_and_rst7_and_pdb_filenames_from_pdb(pdb_file, LES)
  minimized_rst7_file = get_minimized_rst7_filename(pdb_file, LES=LES, minimization_type=minimization_type)
  with tempfolder():
    print('--> command_build: ', ' '.join(command_build))
    output = subprocess.check_output(command_build)
    parm0 = pmd.load_file(prmtop_file, original_rst7_file)
    parm1 = pmd.load_file(prmtop_file, minimized_rst7_file)
    rmsd_data = utils.rmsd(parm0.coordinates, parm1.coordinates)

    aa_eq(rmsd_data, expected_rmsd, decimal=4)
