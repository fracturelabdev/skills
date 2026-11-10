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


# YAML のプレーンスカラーとして解釈できない先頭文字（フロー・引用・ブロック・タグなど）
YAML_INDICATORS = set("[]{}&*!|>'\"%@`,#")
KEY = re.compile(r"[a-z][a-z0-9_-]*")


def parse_frontmatter(text, where="frontmatter"):
    """標準ライブラリだけで、frontmatter が「1 行 1 個の `key: プレーンスカラー`」であることを厳密に検査する。

    YAML として別の型に解釈される値や解析に失敗する値（`[日本語` など）を通さない。
    """
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError(f"{where}: frontmatter がない")
    fm = {}
    for n, line in enumerate(m.group(1).splitlines(), 2):
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        value = value.strip()
        if not sep or not KEY.fullmatch(key):
            raise ValueError(f"{where}:{n}: `key: value` の形でない: {line!r}")
        if key in fm:
            raise ValueError(f"{where}:{n}: キーが重複している: {key}")
        if not value:
            raise ValueError(f"{where}:{n}: 値が空")
        if (value[0] in YAML_INDICATORS or value[:2] in ("- ", "? ", ": ")
                or ": " in value or " #" in value or value.endswith(":")):
            raise ValueError(f"{where}:{n}: YAML のプレーンスカラーとして解釈できない値: {value!r}")
        fm[key] = value
    return fm, m.group(2)


def frontmatter(path):
    return parse_frontmatter(path.read_text(encoding="utf-8"), str(path))


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
        rows = [line for line in t.splitlines() if re.match(r"\| \d{4}-\d{2}-\d{2} \|", line)]
        # 決定は表に追記していくので、今回の行が最終行であることは求めない
        mine = [i for i, line in enumerate(rows) if line.startswith("| 2026-11-10 |") and "`tickets`" in line]
        self.assertEqual(len(mine), 1)
        # 日付は昇順（追記順）に並ぶ
        self.assertEqual([r[2:12] for r in rows], sorted(r[2:12] for r in rows))
        self.assertNotIn("最初のプラグインのテーマと、入れる Skill", t)
        self.assertNotIn("プラグイン名（呼び出し時", t)
        # 既存行（初回コミット時点）が残っている
        old = subprocess.run(["git", "show", "a436f45:DECISIONS.md"], cwd=ROOT,
                             capture_output=True, text=True)
        if old.returncode == 0:
            for line in old.stdout.splitlines():
                if line.startswith("| 2026-10-19"):
                    self.assertIn(line, t)


class FrontmatterParser(unittest.TestCase):
    def test_accepts_plain_scalars(self):
        fm, body = parse_frontmatter("---\nname: issue\ndescription: 日本語の説明「引用」も可\n---\n本文\n")
        self.assertEqual(fm, {"name": "issue", "description": "日本語の説明「引用」も可"})
        self.assertEqual(body, "本文\n")

    def test_rejects_invalid_yaml(self):
        bad = [
            "description: [日本語",
            "description: {a",
            "description: '日本語",
            "description: 説明: 続き",
            "description: 説明 # コメント",
            "description:",
            "名前: issue",
            "name issue",
        ]
        for line in bad:
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_frontmatter(f"---\nname: issue\n{line}\n---\n本文\n")

    def test_rejects_duplicate_key_and_missing_block(self):
        with self.assertRaises(ValueError):
            parse_frontmatter("---\nname: a\nname: b\n---\n本文\n")
        with self.assertRaises(ValueError):
            parse_frontmatter("本文だけ\n")


if __name__ == "__main__":
    unittest.main()
