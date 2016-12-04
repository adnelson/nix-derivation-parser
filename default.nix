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

  servenix = pythonPackages.buildPythonPackage rec {
    name = "servenix-${version}";
    version = "0.4.2";
    src = pkgs.fetchurl {
      url = "https://github.com/adnelson/servenix/archive/0.4.2.tar.gz";
      sha256 = "0skl0kiwkx2fzimad7861ib3l74nhaawfnqr01mfni39c5hvwzyi";
    };
    propagatedBuildInputs = [
      pkgs.coreutils
      pkgs.gzip
      pkgs.nix.out
      pkgs.pv
      pkgs.which
      pythonPackages.flask
      pythonPackages.requests2
      pythonPackages.ipdb
      pythonPackages.six
    ];
    makeWrapperArgs = [
      "--set NIX_BIN_PATH ${pkgs.lib.makeBinPath [pkgs.nix.out]}"
    ];
  };
in

pythonPackages.buildPythonPackage {
  name = "nix_derivation_tools";
  propagatedBuildInputs = [
    pythonPackages.datadiff
    pythonPackages.pyyaml
    pythonPackages.requests2
    rtyaml
    servenix
    pkgs.nix.out
  ];
}
