#include <vector>
#include <string>
#include <boost/python.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/shared_ptr.hpp>
#include "getmdgxfrc.h"
#include <scitbx/vec3.h>
#include <iostream>
#include <scitbx/array_family/ref_reductions.h>
#include <boost/shared_ptr.hpp>


//Class to maintain uform (topology), trajcon (trajectory control settings),
// and mdsys (coordinates, grid, forces) in memory between mdgx calls.
class uform_wrapper
{
public:
  uform_wrapper(std::string prmtop, std::string crdname);
  ~uform_wrapper();
  boost::shared_ptr<uform> uform_ptr;
  boost::shared_ptr<trajcon> trajcon_ptr;
  boost::shared_ptr<mdsys> mdsys_ptr;
  operator uform*(){
          return uform_ptr.get();
  }
};

uform_wrapper::uform_wrapper(std::string prmtop, std::string crdname)
{
  const char * p = prmtop.c_str();
  const char * c = crdname.c_str();
  trajcon_ptr.reset( (trajcon*)malloc(sizeof(trajcon)) );
  *trajcon_ptr=CreateTrajCon();
  uform_ptr.reset( (uform*)malloc(sizeof(uform)) );
  *uform_ptr = LoadTopology(p,trajcon_ptr.get());
  mdsys_ptr.reset( (mdsys*)malloc(sizeof(mdsys)) );
  *mdsys_ptr = CreateMDSys(c, uform_ptr.get() );
}


uform_wrapper::~uform_wrapper()
{
  //printf("Destroying Trajcon\n");
  DestroyTrajCon(trajcon_ptr.get());
  DestroyUform(uform_ptr.get(), mdsys_ptr.get());
  DestroyMDSys(mdsys_ptr.get());
}



//Function to call mdgx main routine.
void callMdgx (std::vector<double>& sites_cart, std::vector<double>& gradients,
               std::vector<double>& target, boost::python::object someuform )
{

        uform_wrapper & U = boost::python::extract<uform_wrapper & > (someuform);
        getmdgxfrc(sites_cart.data(), target.data(), gradients.data(), U, U.trajcon_ptr.get(), U.mdsys_ptr.get() );
}

//Function to convert double flex array to vector of doubles
std::vector<double> ExtractVec (scitbx::af::const_ref<double> const& sites_cart){
        std::vector<double> xyz_flat;
        for (size_t i_seq = 0; i_seq < sites_cart.size(); i_seq++) {
                xyz_flat.push_back(sites_cart[i_seq]);
        }
        return xyz_flat;
}


//Function to print out entire vector of doubles
void printVec (std::vector<double> Vec) {
        std::cout << "[ ";
        for (unsigned int i=0; i < Vec.size(); ++i) {
                std::cout << Vec[i] << ", ";
        }
        std::cout << "]\n";
}








//boost::python registration
#include <boost/python.hpp>
BOOST_PYTHON_MODULE(amber_adaptbx_ext)
{
        using namespace boost::python;
    def("callMdgx", &callMdgx);
    def("ExtractVec", &ExtractVec);
    def("printVec", &printVec);
    //~ class_<std::vector<double> >("VectorOfDouble")
        //~ .def(vector_indexing_suite<std::vector<double> >() );
    boost::python::class_< uform_wrapper >
     ( "uform",
       "c++ class with ptr to topo",
       boost::python::init< std::string, std::string >
       ( boost::python::args("self","prmtop", "crdname"),
         "topo file name; amber coord file name")
     );
}
