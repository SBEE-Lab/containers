import unittest

from scripts.builder.build import _attestation_arguments


class AttestationTest(unittest.TestCase):
    def test_requests_spdx_sbom_and_slsa_v1_provenance(self) -> None:
        self.assertEqual(
            _attestation_arguments(push=True),
            ["--provenance=mode=max,version=v1", "--sbom=true"],
        )

    def test_omits_attestations_from_local_docker_export(self) -> None:
        self.assertEqual(_attestation_arguments(push=False), [])


if __name__ == "__main__":
    unittest.main()
