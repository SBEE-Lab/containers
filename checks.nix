{ pkgs }:
let
  source = pkgs.lib.cleanSource ./.;
in
{
  python-lint =
    pkgs.runCommand "containers-python-lint"
      {
        nativeBuildInputs = with pkgs; [
          mypy
          ruff
        ];
      }
      ''
        cp -r ${source} source
        chmod -R u+w source
        cd source
        ruff check scripts images/*/*.py
        mypy scripts images/*/*.py
        touch $out
      '';

  python-tests =
    pkgs.runCommand "containers-python-tests"
      {
        nativeBuildInputs = with pkgs; [
          git
          python312
        ];
      }
      ''
        cp -r ${source} source
        chmod -R u+w source
        cd source
        export HOME=$TMPDIR
        python -m unittest discover -s scripts -p '*_test.py'
        touch $out
      '';

  workflows-lint =
    pkgs.runCommand "containers-workflows-lint"
      {
        nativeBuildInputs = [ pkgs.actionlint ];
      }
      ''
        cp -r ${source} source
        chmod -R u+w source
        cd source
        actionlint -config-file .github/actionlint.yaml .github/workflows/*.yaml
        touch $out
      '';
}
