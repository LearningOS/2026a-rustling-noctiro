{
  description = "OpenCamp Rustlings community exercises";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    in {
      devShells = nixpkgs.lib.genAttrs systems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = [ pkgs.rustup pkgs.stdenv.cc ];
            shellHook = ''
              export PATH="$HOME/.cargo/bin:$PATH"
              echo "Run bash setup.sh --no-run once, then rustlings."
            '';
          };
        });
    };
}
