{
  nsnix ? import <nsnix> {}
}:

import ./getinputs.nix {
  inherit (nsnix.external) pkgs;
  includeDependenciesOf = [
    nsnix.external.python2.ipython
  ];
}
