{
  pkgs ? import <nixpkgs> {}
}:


pkgs.python3Packages.buildPythonPackage {
  name = "nix-derivation-parser";
  propagatedBuildInputs = [pkgs.nix.out];
  src = ./.;
}
