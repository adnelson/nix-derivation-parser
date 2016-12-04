{
  pkgs ? import <nixpkgs> {},
  python3 ? true,
  pythonPackages ? if python3 then pkgs.python3Packages
                   else pkgs.python2Packages
}:

let
  rtyaml = pythonPackages.buildPythonPackage {
    name = "rtyaml-0.0.3";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/ba/35/d17851c3a79b52379739b71182da24ac29a4cb3f3c2d02ee975c9625db4b/rtyaml-0.0.3.tar.gz";
      sha256 = "0f7d5n3hs0by9rjl9pzkigdr21ml3q8kpd45c302cjm2i9xy2i45";
    };
    propagatedBuildInputs = [pythonPackages.pyyaml];
  };
in

pythonPackages.buildPythonPackage {
  name = "nix_derivation_tools";
  propagatedBuildInputs = [
    pythonPackages.datadiff
    pythonPackages.pyyaml
    rtyaml
  ];
}
