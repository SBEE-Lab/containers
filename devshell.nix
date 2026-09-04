{ pkgs, formatter }:
pkgs.mkShellNoCC {
  packages = with pkgs; [
    curl
    docker-buildx
    docker-client
    gh
    git
    jq
    python312
    skopeo
    syft
    formatter
  ];
}
