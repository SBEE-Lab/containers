{
  description = "containers frequently used for research";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      treefmt-nix,
    }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      treefmtEval = treefmt-nix.lib.evalModule pkgs {
        projectRootFile = "flake.nix";
        programs = {
          deadnix.enable = true;
          keep-sorted.enable = true;
          nixfmt.enable = true;
          ruff-format.enable = true;
          statix.enable = true;
        };
      };
    in
    {
      checks.${system}.formatting = treefmtEval.config.build.check self;

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          cosign
          docker-client
          gh
          git
          jq
          python312
          syft
        ];
      };

      formatter.${system} = treefmtEval.config.build.wrapper;
    };
}
