import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class GitHubActionsWorkflowTest(unittest.TestCase):
    def test_ci_workflow_exists_and_runs_required_commands(self) -> None:
        workflow = ROOT / ".github" / "workflows" / "ci.yml"

        self.assertTrue(workflow.exists(), workflow)
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("push:", text)
        self.assertIn("pull_request:", text)
        self.assertIn("ubuntu-22.04", text)
        self.assertIn("python3 -m unittest discover -s tests -v", text)
        self.assertIn("./scripts/bootstrap-host.sh", text)
        self.assertIn("python3 rebuild/driver.py build", text)
        self.assertIn("./scripts/verify.sh", text)
        self.assertIn("actions/checkout@v5", text)
        self.assertIn("actions/upload-artifact@v6", text)


if __name__ == "__main__":
    unittest.main()
