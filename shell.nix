{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.rustup pkgs.stdenv.cc ];
  shellHook = ''
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "Run bash setup.sh --no-run once, then rustlings."
  '';
}
