from pathlib import Path
import unittest


class WebPackagingTests(unittest.TestCase):
    def test_browserfs_is_available_at_pygbag_cdn_path(self):
        browserfs = Path("static/cdn/0.9.3/browserfs.min.js")

        self.assertTrue(browserfs.is_file())
        self.assertGreater(browserfs.stat().st_size, 100_000)

    def test_web_helper_skips_pygbag_gray_user_engagement_gate(self):
        script = Path("web.sh").read_text()
        readme = Path("README.md").read_text()

        self.assertIn("--ume_block 0", script)
        self.assertIn("--template static/sudoku.tmpl", script)
        self.assertIn("--template static/sudoku.tmpl", readme)

    def test_custom_template_replaces_pygbag_green_startup_prompt(self):
        template = Path("static/sudoku.tmpl").read_text()

        self.assertIn("sudoku-preloader", template)
        self.assertIn("drawSudokuPreloader", template)
        self.assertIn("cellOrder", template)
        self.assertIn("Math.random()", template)
        self.assertIn("max-width: 100vw", template)
        self.assertIn("max-height: 100vh", template)
        self.assertIn("rgb(252, 248, 235)", template)
        self.assertNotIn("Ready to start ! Please click/touch page", template)
        self.assertNotIn("background: green", template)
        self.assertNotIn("Loading, please wait ...", template)

    def test_pygbag_entry_point_runs_without_main_guard(self):
        main_py = Path("main.py").read_text()

        self.assertIn("import pygame", main_py)
        self.assertIn("\nasyncio.run(main())", main_py)
        self.assertNotIn('if __name__ == "__main__"', main_py)


if __name__ == "__main__":
    unittest.main()
