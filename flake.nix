{
  description = "containers frequently used for research";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      treefmt-nix,
    }:
    let
      inherit (nixpkgs) lib;

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      eachSystem = lib.genAttrs systems;

      flake = self // {
        inherit inputs;
      };

      pkgsFor = eachSystem (system: import nixpkgs { inherit system; });

      scopes = eachSystem (
        system:
        let
          pkgs = pkgsFor.${system};
          treefmtEval = treefmt-nix.lib.evalModule pkgs {
            projectRootFile = "flake.nix";
            settings.global.excludes = [ "images/*/src/**" ];
            programs = {
              deadnix.enable = true;
              keep-sorted.enable = true;
              nixfmt.enable = true;
              ruff-check.enable = true;
              ruff-format.enable = true;
              statix.enable = true;
            };
          };
        in
        lib.makeScope pkgs.newScope (self: {
          inherit flake inputs system;
          formatter = treefmtEval.config.build.wrapper;
          formatting = treefmtEval.config.build.check flake;
          devshell = self.callPackage ./devshell.nix { };
          checks = self.callPackage ./checks.nix { };
        })
      );
    in
    {
      checks = eachSystem (
        system:
        scopes.${system}.checks
        // {
          formatting = scopes.${system}.formatting;
          devshell-default = scopes.${system}.devshell;
        }
      );

      devShells = eachSystem (system: {
        default = scopes.${system}.devshell;
      });

      formatter = eachSystem (system: scopes.${system}.formatter);
    };
}
