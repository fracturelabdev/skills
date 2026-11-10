#!/usr/bin/env python3
"""構造検査（標準ライブラリのみ、秘密情報不要）。実行: python3 tests/test_structure.py"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "tickets"
SKILLS = ["issue", "pr", "docs"]
JA = re.compile(r"[぀-ヿ一-鿿]")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    assert m, f"{path}: frontmatter がない"
    fm = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in fm.items()}, m.group(2)


class Structure(unittest.TestCase):
    def test_manifest(self):
        d = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(d["name"], "tickets")
        self.assertEqual(sorted(p.name for p in (PLUGIN / ".claude-plugin").iterdir()), ["plugin.json"])

    def test_skills(self):
        found = sorted(p.parent.name for p in (PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(found, sorted(SKILLS))
        for s in SKILLS:
            fm, body = frontmatter(PLUGIN / "skills" / s / "SKILL.md")
            self.assertEqual(fm["name"], s)
            self.assertTrue(JA.search(fm["description"]))
            self.assertTrue(JA.search(body))
            self.assertNotIn("disable-model-invocation", fm)
            self.assertNotIn("user-invokable", fm)
            self.assertFalse(set(fm) - {"name", "description", "when_to_use"})

    def test_no_personal_paths(self):
        for p in PLUGIN.rglob("*"):
            if p.is_file():
                self.assertNotIn("~/.claude", p.read_text(encoding="utf-8"), p)

    def test_marketplace(self):
        d = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(d["name"], "fracturelab")
        e = [p for p in d["plugins"] if p["name"] == "tickets"]
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0]["source"], "./plugins/tickets")

    def test_readme(self):
        t = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertRegex(t, r"(?m)^\|.*`tickets`.*\|")
        self.assertNotIn("（準備中）", t)
        self.assertIn("claude plugin marketplace add fracturelabdev/skills", t)
        self.assertIn("claude plugin install tickets@fracturelab", t)

    def test_decisions(self):
        t = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        last = t.rstrip("\n").splitlines()[-1]
        self.assertTrue(last.startswith("| 2026-11-10 |"))
        self.assertIn("`tickets`", last)
        self.assertNotIn("最初のプラグインのテーマと、入れる Skill", t)
        self.assertNotIn("プラグイン名（呼び出し時", t)
        # 既存行（初回コミット時点）が残っている
        old = subprocess.run(["git", "show", "a436f45:DECISIONS.md"], cwd=ROOT,
                             capture_output=True, text=True)
        if old.returncode == 0:
            for line in old.stdout.splitlines():
                if line.startswith("| 2026-10-19"):
                    self.assertIn(line, t)


if __name__ == "__main__":
    unittest.main()
