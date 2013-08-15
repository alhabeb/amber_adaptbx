#! /bin/bash

cat >params.eff <<EOF
refinement {
  main {
    number_of_macro_cycles=1
  }
  refine {
    strategy = *individual_sites individual_sites_real_space rigid_body \
               individual_adp group_adp tls occupancies group_anomalous
    adp {
      individual {
        anisotropic = "not (element H)"
	isotropic = "element H"
      }
    }
  }
  bulk_solvent_and_scale {
    bulk_solvent = False
    anisotropic_scaling = False
    k_sol_b_sol_grid_search = False
    minimization_k_sol_b_sol = False
  }
}
EOF

phenix.refine 4lzt.pdb prefix=vs_obs 4lzt-sf-truncated.mtz params.eff refinement.input.xray_data.r_free_flags.file_name=md_avg_95_rfree.mtz --overwrite
