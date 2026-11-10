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
LINE = re.compile(r"([a-z][a-z0-9_-]*): (.*)")
# YAML が文字列以外に解決するプレーンスカラー。YAML 1.1（PyYAML の implicit resolver）と
# YAML 1.2 core schema（仕様と ruamel.yaml の実装）の和集合で、どれか 1 つでも文字列に
# ならない値を拒否する。仕様にあって実装が解決しない値（`y` `.1e7` など）も安全側で拒否する。
NON_STRING = re.compile("|".join([
    # bool（1.1 / 1.2）
    r"yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF|y|Y|n|N",
    # null・merge・value（1.1）
    r"~|null|Null|NULL|<<|=",
    # int（1.1: 2 / 8 / 10 / 16 進と 60 進）
    r"[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+",
    r"[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+",
    # int（1.2 core: 先頭 0 の 10 進・0o・0x）
    r"[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+",
    # float（1.1）
    r"[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?",
    r"[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*",
    # float（1.2 core）
    r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?",
    # int / float（ruamel.yaml の 1.2 resolver。仕様より広く `_` を受け付ける）
    r"[-+]?0o?[0-7_]+|[-+][0-9_]+|[0-9][0-9_]*",
    r"[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+]?[0-9]+)?|[-+]?[0-9][0-9_]*[eE][-+]?[0-9]+"
    r"|[-+]?\.[0-9_]+(?:[eE][-+][0-9]+)?",
    r"[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)",
    # timestamp（1.1）。時刻が付くのは HH:MM:SS が続くときだけ
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
    r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?"
    r"(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?",
]))


def parse_frontmatter(text, where="frontmatter"):
    """標準ライブラリだけで、frontmatter が「1 行 1 個の `key: プレーンスカラー`」であることを厳密に検査する。

    コロンの直後に空白が無い行、解析に失敗する値（`[日本語` など）、
    文字列以外に解決する値（`true` `null` `1` `2026-11-10` など）を通さない。
    """
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError(f"{where}: frontmatter がない")
    fm = {}
    for n, line in enumerate(m.group(1).splitlines(), 2):
        if not line.strip():
            continue
        lm = LINE.fullmatch(line.rstrip())
        if not lm:
            raise ValueError(f"{where}:{n}: `key: value`（コロンの後に空白）の形でない: {line!r}")
        key, value = lm.group(1), lm.group(2).strip()
        if key in fm:
            raise ValueError(f"{where}:{n}: キーが重複している: {key}")
        if not value:
            raise ValueError(f"{where}:{n}: 値が空")
        if (value[0] in YAML_INDICATORS or value[:2] in ("- ", "? ", ": ")
                or ": " in value or " #" in value or value.endswith(":")):
            raise ValueError(f"{where}:{n}: YAML のプレーンスカラーとして解釈できない値: {value!r}")
        if NON_STRING.fullmatch(value):
            raise ValueError(f"{where}:{n}: YAML で文字列以外に解決される値: {value!r}")
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
        # 取れないとき（shallow clone など）に黙って飛ばさない
        self.assertEqual(old.returncode, 0,
                         f"a436f45 の DECISIONS.md を読めない（完全な履歴が必要: git fetch --unshallow）: {old.stderr}")
        kept = [line for line in old.stdout.splitlines() if line.startswith("| 2026-10-19")]
        self.assertEqual(len(kept), 5)
        for line in kept:
            self.assertIn(line, t)


class FrontmatterParser(unittest.TestCase):
    def test_accepts_plain_scalars(self):
        fm, body = parse_frontmatter("---\nname: issue\ndescription: 日本語の説明「引用」も可\n---\n本文\n")
        self.assertEqual(fm, {"name": "issue", "description": "日本語の説明「引用」も可"})
        self.assertEqual(body, "本文\n")
        # YAML でも文字列のままの値は通す
        for value in ["2026-11-10 の案内", "2026-11-10T", ".", "yEs", "1.2.3", "v1", "0x", "1:60"]:
            with self.subTest(value=value):
                fm, _ = parse_frontmatter(f"---\nname: issue\ndescription: {value}\n---\n本文\n")
                self.assertEqual(fm["description"], value)

    def test_rejects_invalid_yaml(self):
        bad = [
            "description: [日本語",
            "description: {a",
            "description: '日本語",
            "description: 説明: 続き",
            "description: 説明 # コメント",
            "description:",
            "description:日本語の説明",
            "description: true",
            "description: null",
            "description: ~",
            "description: 1",
            "description: 0x1F",
            "description: 1.5",
            "description: .inf",
            "description: 2026-11-10",
            "description: 2026-11-10 12:30:00",
            "description: 2026-11-10T12:30:00Z",
            "description: 1:20",
            "description: 1:23:45",
            "description: 12:30:00",
            "description: 08",
            "description: 0o17",
            "description: -1.5e+3",
            "description: 1e3",
            "description: <<",
            "description: =",
            "when_to_use: Yes",
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
