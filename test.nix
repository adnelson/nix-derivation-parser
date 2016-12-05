with import <nixpkgs> {};
with stdenv;

mkDerivation {
  name = "tester";
  buildInputs = [hello perl];
  buildCommand = ''
    echo "Not meant to be built!"
    exit 1
  '';
}
