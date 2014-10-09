from __future__ import division
from libtbx import group_args
import sys, os
import iotbx.pdb
import argparse
from scitbx.array_family import flex
import scitbx.restraints
import boost.python
ext = boost.python.import_ext("amber_adaptbx_ext")
import sander
from chemistry.amber.readparm import AmberParm, Rst7


master_phil_str = """
  use_amber = False
    .type = bool
  topology_file_name = None
    .type = path
  coordinate_file_name = None
    .type = path
  use_sander = False
    .type = bool
"""

class geometry_manager(object):

  def __init__(self,
        sites_cart=None,
        energy_components=None,
        gradients=None,
        number_of_restraints=0,
        gradients_factory=flex.vec3_double,
        amber_structs=None):
    self.sites_cart = sites_cart
    self.energy_components = energy_components
    self.gradients_factory = gradients_factory
    self.number_of_restraints=number_of_restraints
    self.amber_structs=amber_structs

    if self.energy_components is None:
      self.energy_components = flex.double([0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])
  def energies_sites(self,
        crystal_symmetry,
        compute_gradients=False):
    # import code; code.interact(local=dict(globals(), **locals()))
    #Expand sites_cart to unit cell
    sites_cart_uc=expand_coord_to_unit_cell(self.sites_cart, crystal_symmetry)

    if hasattr(self.amber_structs,'parm'):
      # print "\n\nUSING SANDER\n\n"
      sander_coords = list(sites_cart_uc.as_double())
      # import code; code.interact(local=dict(globals(), **locals()))
      sander.set_positions(sander_coords)
      ene, frc = sander.energy_forces()
      # sander.cleanup()
      if (compute_gradients) :
        gradients_uc=flex.vec3_double(flex.double(frc)) * -1
        gradients = gradients_uc[0:self.sites_cart.size()]
        # gradients = collapse_grad_to_asu(gradients_uc, crystal_symmetry)
      else :
        gradients = self.gradients_factory(
          flex.double(self.sites_cart.size() * 3,0))
      result = energies(
        compute_gradients=compute_gradients,
        gradients=gradients,
        gradients_size=None,
        gradients_factory=None,
        normalization=False)
      result.number_of_restraints = self.number_of_restraints
      result.residual_sum = ene.tot
      ptrfunc = self.amber_structs.parm.ptr
      nbond = ptrfunc('nbonh') + ptrfunc('nbona')
      nangl = ptrfunc('ntheth') + ptrfunc('ntheta')
      nmphi = ptrfunc('nphih') + ptrfunc('nphia')
      result.energy_components = [ene.tot, ene.bond, ene.angle, ene.dihedral,
                                  ene.elec + ene.elec_14, ene.vdw + ene.vdw_14,
                                  nbond, nangl, nmphi]
      result.finalize_target_and_gradients()

    else:
      # print "\n\nUSING MDGX\n\n"
      #Convert flex arrays to C arrays
      sites_cart_c=ext.ExtractVec(sites_cart_uc.as_double())
      gradients_c=ext.ExtractVec(flex.double(sites_cart_uc.size() * 3, 0))
      energy_components_c=ext.ExtractVec(self.energy_components)

      # Call c++ interface to call mdgx to calculate new gradients and target
      ext.callMdgx(sites_cart_c, gradients_c, energy_components_c, self.amber_structs)
      if (compute_gradients) :
        # import code; code.interact(local=dict(globals(), **locals()))
        # sys.exit()
        gradients_uc = self.gradients_factory(gradients_c) * -1
        gradients = gradients_uc[0:self.sites_cart.size()]
        # gradients = collapse_grad_to_asu(gradients_uc, crystal_symmetry)
      else :
        gradients = self.gradients_factory(
          flex.double(self.sites_cart.size() * 3,0))
      result = energies(
        compute_gradients=compute_gradients,
        gradients=gradients,
        gradients_size=None,
        gradients_factory=None,
        normalization=False)
      result.number_of_restraints = self.number_of_restraints
      result.residual_sum = float(energy_components_c[0])
      result.energy_components = list(energy_components_c)
      result.finalize_target_and_gradients()
    return result

class energies (scitbx.restraints.energies) :
  def __init__ (self, *args, **kwds) :
    scitbx.restraints.energies.__init__(self, *args, **kwds)
    self.energy_components = None

  def show(self):
    print "    Amber total energy: %0.2f" %(self.residual_sum)
    print "      bonds (n=%d): %0.2f" %(self.energy_components[6],
                                             self.energy_components[1])
    print "      angles (n=%d): %0.2f" %(self.energy_components[7],
                                             self.energy_components[2])
    print "      dihedrals (n=%d): %0.2f" %(self.energy_components[8],
                                             self.energy_components[3])
    print "      electrostatics: %0.2f" %(self.energy_components[4])
    print "      van der Waals: %0.2f" %(self.energy_components[5])
    return 0
    
  def get_grms(self):
    from math import sqrt
    gradients_1d = self.gradients.as_double()
    grms = sum(gradients_1d**2)
    grms /= gradients_1d.size()
    grms = sqrt(grms)
    return grms

def print_sites_cart(sites_cart):
        for atom in sites_cart:
                print("%8.3f%8.3f%8.3f"%(atom[0], atom[1], atom[2]))

def get_amber_structs (parm_file_name, rst_file_name):
        return ext.uform(parm_file_name, rst_file_name)

class sander_structs ():
  def __init__ (self, parm_file_name, rst_file_name):
    self.parm = AmberParm(parm_file_name)
    self.rst = Rst7.open(rst_file_name)
    self.inp = sander.pme_input()

def expand_coord_to_unit_cell(sites_cart, crystal_symmetry):
  sites_cart_uc = flex.vec3_double()
  cell = crystal_symmetry.unit_cell()
  sg = crystal_symmetry.space_group()
  for i, op in enumerate(sg.all_ops()):
    rotn = op.r().as_double()
    tln = cell.orthogonalize(op.t().as_double())
    # import code; code.interact(local=dict(globals(), **locals()))
    # sys.exit()
    sites_cart_uc.extend( (rotn * sites_cart) + tln)
  return sites_cart_uc
    
def collapse_grad_to_asu(gradients_uc, crystal_symmetry):
  cell = crystal_symmetry.unit_cell()
  sg = crystal_symmetry.space_group()
  n_symop = sg.n_smx()
  n_asu_atoms = int(gradients_uc.size() / n_symop)
  # import code; code.interact(local=dict(globals(), **locals()))
  # sys.exit()
  gradients = flex.vec3_double(n_asu_atoms)
  for i, op in enumerate(sg.all_ops()):
    inv_rotn = op.r().inverse().as_double()
    tln = cell.orthogonalize(op.t().as_double())
    start = i*n_asu_atoms
    end = (i+1)*n_asu_atoms
    gradients += inv_rotn * (gradients_uc[start:end])
  gradients = gradients * (1.0/n_symop)
  return gradients

def bond_angle_rmsd(parm, sites_cart):
  from math import acos, pi, sqrt

  #bond rmsd
  bdev = 0
  # import code; code.interact(local=dict(globals(), **locals()))
  # sys.exit()
  for i, bond in enumerate(parm.bonds_inc_h + parm.bonds_without_h):
    atom1 = sites_cart[bond.atom1.starting_index]
    atom2 = sites_cart[bond.atom2.starting_index]
    dx = atom1[0] - atom2[0]
    dy = atom1[1] - atom2[1]
    dz = atom1[2] - atom2[2]
    contrib = bond.bond_type.req - sqrt(dx*dx + dy*dy + dz*dz)
    bdev += contrib * contrib
  nbond = i + 1
  bdev /= nbond
  bdev = sqrt(bdev)

  #angle rmsd
  adev = 0
  for i, angle in enumerate(parm.angles_inc_h + parm.angles_without_h):
    atom1 = sites_cart[angle.atom1.starting_index]
    atom2 = sites_cart[angle.atom2.starting_index]
    atom3 = sites_cart[angle.atom3.starting_index]
    a = [ atom1[0]-atom2[0], atom1[1]-atom2[1], atom1[2]-atom2[2] ]
    b = [ atom3[0]-atom2[0], atom3[1]-atom2[1], atom3[2]-atom2[2] ]
    a = flex.double(a)
    b = flex.double(b)
    contrib = angle.angle_type.theteq - acos(a.dot(b)/(a.norm()*b.norm()))
    contrib *= 180/pi
    adev += contrib * contrib
  nang = i + 1
  adev /= nang
  adev = sqrt(adev)

  return bdev, adev


def run(pdb,prmtop, crd):

  #===================================================================#
  #                                                                   #
  #  BEFORE C++                                                       #
  #                                                                   #
  #===================================================================#

  #file i/o
  pdb_file = os.path.abspath(pdb)
  pdb_inp = iotbx.pdb.input(file_name=pdb_file)
  pdb_atoms = pdb_inp.atoms_with_labels()
  symm = pdb_inp.crystal_symmetry()
  xray_structure = pdb_inp.xray_structure_simple(enable_scattering_type_unknown=True)


  #     initiate flex arrays for coordinates, gradients, energy
  sites_cart=xray_structure.sites_cart()
  gradients=flex.double(len(sites_cart)*3)
  target=flex.double([6.7,1.0,2.0,3.0,4.0,5.0,0.0,0.0,0.0,0.0])
  print "Number of atom sites: %d " %sites_cart.size()
  print "\nGradients and target BEFORE C call:"
  print list(gradients[1:10])
  print target[0]

  #===================================================================#
  #                                                                   #
  #  CALL C++                                                         #
  #                                                                   #
  #===================================================================#

  U=ext.uform(prmtop, crd)

  #Convert flex arrays to C arrays
  sites_cart_c=ext.ExtractVec(sites_cart.as_double())
  gradients_c=ext.ExtractVec(gradients)
  target_c=ext.ExtractVec(target)

  # Call c++ interface to call mdgx to calculate new gradients and target
  ext.callMdgx(sites_cart_c, gradients_c, target_c, U)

  # Convert back into python types (eg. into flex arrays for phenix to use)
  gradients=flex.vec3_double(gradients_c)*-1

  target= flex.double(target_c)

  #===================================================================#
  #                                                                   #
  #  AFTER C++                                                        #
  #                                                                   #
  #===================================================================#


  print "\nGradients and target AFTER C call:"
  print list(gradients[0:10])
  print target[0]
  print target[9]

  print "Amber_total_energy: %7.6f"             %(target[0])
  print "  bonds (n= ): %7.6f"                  %(target[1])
  print "  angles (n= ): %7.6f"                         %(target[2])
  print "  dihedrals (n= ): %7.6f"              %(target[3])
  print "  electrostatics: %7.6f"               %(target[4])
  print "  vanderWaals: %7.6f"                  %(target[5])

  return 0

if __name__ == "__main__" :
        parser = argparse.ArgumentParser()
        parser.add_argument("pdb", help="name of pdb file")
        parser.add_argument("prmtop", help="name of topology file")
        parser.add_argument("crd", help="name of coordinate file")
        args = parser.parse_args()
        run(args.pdb,args.prmtop, args.crd)
