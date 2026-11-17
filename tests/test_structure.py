#!/usr/bin/env python3
"""構造検査（標準ライブラリのみ、秘密情報不要）。実行: python3 tests/test_structure.py"""
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "tickets"
SKILLS = ["issue", "pr", "docs"]
JA = re.compile(r"[぀-ヿ一-鿿]")
# プラグインの実体として数えない OS 生成物。先頭が . の隠しファイルは別途除く。
OS_GENERATED = {"thumbs.db", "ehthumbs.db", "desktop.ini"}
# marketplace 雛形で入った決定。shallow clone でも比較できるよう、コミットではなくこの定数を正とする
BASELINE_DECISIONS = [
    "| 2026-10-19 | repo は `fracturelabdev/skills`、最初から public | 少しずつ足していく前提。足すたびに `FLB-ORG-002` §I（差分）を通す |",
    "| 2026-10-19 | 1 repo に marketplace を 1 つ置き、テーマ別に複数プラグインを置く | 利用者は必要なテーマだけ入れられ、管理する repo は 1 つで済む |",
    "| 2026-10-19 | marketplace 名は `fracturelab` | インストール名が `<plugin>@fracturelab` になる |",
    "| 2026-10-19 | プラグインは `plugins/<name>/` に置く | 公式の marketplace 構成例に合わせる |",
    "| 2026-10-19 | 日本語のみ | 想定利用者は日本語話者 |",
]


# YAML のプレーンスカラーとして解釈できない先頭文字（フロー・引用・ブロック・タグなど）
YAML_INDICATORS = set("[]{}&*!|>'\"%@`,#")
LINE = re.compile(r"([a-z][a-z0-9_-]*): (.*)")
# YAML が文字列以外に解決するプレーンスカラー。YAML 1.1（PyYAML の implicit resolver）と
# YAML 1.2 core schema（仕様と ruamel.yaml の実装）の和集合で、どれか 1 つでも文字列に
# ならない値を拒否する。仕様にあって実装が解決しない値（`y` `.1e7` など）と、
# 仕様上は文字列の符号付き NaN（`-.nan` `+.NaN` `+.NAN`）も安全側で拒否する。
def compile_non_string(parts):
    """選択肢を `|` で連結する。空の選択肢（`||`、先頭や末尾の `|`）は拒否する。

    断片を文字列連結するとき、次の断片を `|` で始めない。`"|".join` が間に
    `|` を足すので、先頭の `|` と重なると空の選択肢になる。
    """
    for part in parts:
        if not part or part.startswith("|") or part.endswith("|") or "||" in part:
            raise ValueError(f"空の選択肢がある: {part!r}")
    return re.compile("|".join(parts))


NON_STRING = compile_non_string([
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
    r"[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?",
    r"\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?",
    r"[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*",
    # float（1.2 core）
    r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?",
    # int / float（ruamel.yaml の 1.2 resolver。仕様より広く `_` を受け付ける）
    r"[-+]?0o?[0-7_]+|[-+][0-9_]+|[0-9][0-9_]*",
    r"[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+]?[0-9]+)?",
    r"[-+]?[0-9][0-9_]*[eE][-+]?[0-9]+",
    r"[-+]?\.[0-9_]+(?:[eE][-+][0-9]+)?",
    # inf は仕様どおり符号付き。nan は YAML 1.1 / 1.2 core も PyYAML / ruamel.yaml も
    # 符号なし（.nan .NaN .NAN）だけを float にする。符号付きを float にする実装があるため、
    # -.nan +.NaN +.NAN を含む符号付きも拒否する。
    r"[-+]?\.(?:inf|Inf|INF)|[-+]?\.(?:nan|NaN|NAN)",
    # timestamp（1.1）。時刻が付くのは HH:MM:SS が続くときだけ
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
    r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?"
    r"(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?",
])


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
        # YAML の空白はスペースとタブだけ。タブは区切りの判定を崩すので行ごと拒否し、
        # 全角スペースなど YAML が文字として残すものは削らない
        if "\t" in line:
            raise ValueError(f"{where}:{n}: タブを含む: {line!r}")
        if not line.strip(" "):
            continue
        lm = LINE.fullmatch(line.rstrip(" "))
        if not lm:
            raise ValueError(f"{where}:{n}: `key: value`（コロンの後に空白）の形でない: {line!r}")
        key, value = lm.group(1), lm.group(2).strip(" ")
        if key in fm:
            raise ValueError(f"{where}:{n}: キーが重複している: {key}")
        if not value:
            raise ValueError(f"{where}:{n}: 値が空")
        if (value[0] in YAML_INDICATORS or value[:2] in ("- ", "? ", ": ") or value in ("-", "?")
                or ": " in value or " #" in value or value.endswith(":")):
            raise ValueError(f"{where}:{n}: YAML のプレーンスカラーとして解釈できない値: {value!r}")
        if NON_STRING.fullmatch(value):
            raise ValueError(f"{where}:{n}: YAML で文字列以外に解決される値: {value!r}")
        fm[key] = value
    return fm, m.group(2)


def frontmatter(path):
    return parse_frontmatter(path.read_text(encoding="utf-8"), str(path))


def is_plugin_content_name(name):
    """隠しファイル（`.DS_Store` など）と OS の生成物でなければ True。"""
    return not name.startswith(".") and name.lower() not in OS_GENERATED


def listed_plugin_files(directory):
    """隠しファイル（`.DS_Store` など）と OS の生成物を除いたエントリ名。"""
    return sorted(p.name for p in directory.iterdir() if is_plugin_content_name(p.name))


# README の「個人の環境（特定のパス）」に合わせ、~/.claude だけを見ない。
# ホーム相対（~/... と ~user/...）、macOS / Linux / Windows のユーザーディレクトリ。
PERSONAL_PATH = re.compile(
    r"~/[^\s`\"')\]]+"
    r"|~[A-Za-z0-9][A-Za-z0-9._-]*/[^\s`\"')\]]*"
    r"|/(?:Users|home)/[^\s`\"')\]]+"
    r"|[A-Za-z]:[\\/]Users[\\/][^\s`\"')\]]*"
)


def personal_path_problems(directory):
    """実ファイルに個人環境のパスがあるか、UTF-8 として読めないかを返す。

    隠しファイルと OS 生成物は `listed_plugin_files` と同じ基準で読まない。
    親ディレクトリが `.claude-plugin` でも、実ファイル（`plugin.json` など）は読む。
    それ以外でデコードできないファイルは黙って飛ばさない。文字として判定できないので
    本文は検索せず、「UTF-8 として読めない」として返す。`UnicodeDecodeError` は出さない。
    """
    problems = []
    files = sorted(
        p for p in directory.rglob("*") if p.is_file() and is_plugin_content_name(p.name)
    )
    for p in files:
        shown = p.relative_to(directory).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"{shown}: UTF-8 として読めない")
            continue
        match = PERSONAL_PATH.search(text)
        if match:
            problems.append(f"{shown}: 個人環境のパスを含む ({match.group(0)})")
    return problems


class Structure(unittest.TestCase):
    def test_manifest(self):
        d = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(d["name"], "tickets")
        # 必要な plugin.json 以外の実ファイルが無いこと。隠しファイルと OS の生成物では落とさない。
        self.assertEqual(listed_plugin_files(PLUGIN / ".claude-plugin"), ["plugin.json"])

    def test_listed_plugin_files_skips_hidden_and_os_junk(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "plugin.json").write_text("{}", encoding="utf-8")
            (root / ".DS_Store").write_bytes(b"")
            (root / "._plugin.json").write_bytes(b"")
            (root / "Thumbs.db").write_bytes(b"")
            (root / "desktop.ini").write_bytes(b"")
            (root / "extra.txt").write_text("x", encoding="utf-8")
            self.assertEqual(listed_plugin_files(root), ["extra.txt", "plugin.json"])

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
        self.assertEqual(personal_path_problems(PLUGIN), [])

    def test_personal_path_problems_skip_junk_and_flag_undecodable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            plugin_dir = root / ".claude-plugin"
            plugin_dir.mkdir()
            manifest = plugin_dir / "plugin.json"
            manifest.write_text('{"name": "tickets"}\n', encoding="utf-8")
            skill = root / "skills" / "issue"
            skill.mkdir(parents=True)
            guide = skill / "SKILL.md"
            guide.write_text("日本語の手順\n", encoding="utf-8")
            # 隠しファイルと OS 生成物は、バイナリでも個人パスを含んでいても読まない。
            (root / ".DS_Store").write_bytes(b"\xff\xfe~/.claude\x00")
            (plugin_dir / ".DS_Store").write_bytes(b"\x80~/.claude")
            (skill / "._SKILL.md").write_bytes(b"\xff~/.claude")
            (skill / "Thumbs.db").write_bytes(b"\xff~/.claude")
            (root / "EhThumbs.db").write_bytes(b"~/.claude")
            (plugin_dir / "Desktop.ini").write_text("~/.claude\n", encoding="utf-8")

            with self.subTest("os junk"):
                self.assertEqual(personal_path_problems(root), [])

            binary = skill / "diagram.bin"
            # ASCII の個人パスを含むが UTF-8 ではない。別エンコーディングで検索して通さない。
            binary.write_bytes(b"\xff~/.claude")
            with self.subTest("undecodable"):
                self.assertEqual(
                    personal_path_problems(root),
                    ["skills/issue/diagram.bin: UTF-8 として読めない"],
                )

            binary.write_text("手元の ~/.claude を参照する\n", encoding="utf-8")
            with self.subTest("text hit"):
                self.assertEqual(
                    personal_path_problems(root),
                    ["skills/issue/diagram.bin: 個人環境のパスを含む (~/.claude)"],
                )

            binary.write_text("参照しない\n", encoding="utf-8")
            manifest.write_text("~/.claude\n", encoding="utf-8")
            with self.subTest("hidden directory still scanned"):
                self.assertEqual(
                    personal_path_problems(root),
                    [".claude-plugin/plugin.json: 個人環境のパスを含む (~/.claude)"],
                )

            manifest.write_text('{"name": "tickets"}\n', encoding="utf-8")
            samples = [
                ("~/Documents/memo.md", "~/Documents/memo.md"),
                ("/Users/ada/notes.md", "/Users/ada/notes.md"),
                ("/home/ada/.config", "/home/ada/.config"),
                ("C:\\Users\\ada\\notes", "C:\\Users\\ada\\notes"),
                ("~ada/notes.md", "~ada/notes.md"),
            ]
            for text, shown in samples:
                binary.write_text(text + "\n", encoding="utf-8")
                with self.subTest(text=text):
                    self.assertEqual(
                        personal_path_problems(root),
                        [f"skills/issue/diagram.bin: 個人環境のパスを含む ({shown})"],
                    )

            binary.write_text(
                "手順は docs/dev/setup.md と https://github.com/fracturelabdev/skills\n",
                encoding="utf-8",
            )
            with self.subTest("ordinary paths"):
                self.assertEqual(personal_path_problems(root), [])

    def test_marketplace(self):
        d = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(d["name"], "fracturelab")
        e = [p for p in d["plugins"] if p["name"] == "tickets"]
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0]["source"], "./plugins/tickets")
        # plugin.json と同じ display fields。author は name 必須のオブジェクト、license は SPDX 文字列。
        author = e[0]["author"]
        self.assertIsInstance(author, dict)
        self.assertTrue(author["name"].strip())
        self.assertTrue(author["url"].startswith("https://"))
        self.assertLessEqual(set(author), {"name", "email", "url"})
        self.assertIsInstance(e[0]["license"], str)
        self.assertEqual(e[0]["license"], "MIT")

    def test_readme(self):
        t = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertRegex(t, r"(?m)^\|.*`tickets`.*\|")
        self.assertNotIn("（準備中）", t)
        self.assertIn("claude plugin marketplace add fracturelabdev/skills", t)
        self.assertIn("claude plugin install tickets@fracturelab", t)

    def test_guidance_matches_sources(self):
        docs = (PLUGIN / "skills" / "docs" / "SKILL.md").read_text(encoding="utf-8")
        issue = (PLUGIN / "skills" / "issue" / "SKILL.md").read_text(encoding="utf-8")
        pr = (PLUGIN / "skills" / "pr" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "命名、同じ内容を 2 箇所に書かないこと、空のディレクトリを作らないこと、"
            "個人環境のパスを書かないことは、「守ること」として常に適用する。",
            docs,
        )
        self.assertIn("両方あるときにルート側へ移さない。", docs)
        self.assertNotIn("以下は使わない", docs)

        self.assertIn("4 点と 5 点も分ける", issue)
        self.assertIn("4 点と 5 点は分けない", issue)
        self.assertIn("4 点と 5 点は分けず", issue)
        self.assertIn("同じシェルプロセスで続ける", issue)
        self.assertIn("既にある EXIT trap を消して置き換わる", issue)
        self.assertIn("必須引数はラベル名だけである", issue)
        self.assertIn("ページごとの出力を続けたものが全件になる", issue)

        headings = [
            "## 対応 Issue",
            "## 変更概要",
            "## 完了条件の充足",
            "## 検証証跡",
            "## レビュー観点",
            "## 補足（任意・200字以内）",
        ]
        positions = [pr.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("この形式では作らない", pr)
        self.assertIn("件名の形式を変えても作らない", pr)
        self.assertIn("`Refs #N` | 書かない | 書かない |", pr)

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
        # 2026-10-19 の 5 行。git の履歴を引かず、この文字列がこの順で残っていることだけを見る
        pos = 0
        for line in BASELINE_DECISIONS:
            i = t.find(line, pos)
            self.assertGreaterEqual(i, 0, line)
            pos = i + len(line)


class FrontmatterParser(unittest.TestCase):
    def test_accepts_plain_scalars(self):
        fm, body = parse_frontmatter("---\nname: issue\ndescription: 日本語の説明「引用」も可\n---\n本文\n")
        self.assertEqual(fm, {"name": "issue", "description": "日本語の説明「引用」も可"})
        self.assertEqual(body, "本文\n")
        # YAML でも文字列のままの値は通す
        for value in ["2026-11-10 の案内", "2026-11-10T", ".", "yEs", "1.2.3", "v1", "0x", "1:60",
                      "\u3000全角スペースで始まる説明", "説明\u00a0#ではない"]:
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
            "description: .nan",
            "description: .NaN",
            "description: .NAN",
            "description: -.nan",
            "description: +.NaN",
            "description: +.NAN",
            "description: +.nan",
            "description: -.NaN",
            "description: -.NAN",
            "description: 2026-11-10",
            "description: 2026-11-10 12:30:00",
            "description: 2026-11-10T12:30:00Z",
            "description: 説明:\t続き",
            "description: 説明\t#コメント",
            "description: -\t項目",
            "description:\t説明",
            "description: -",
            "description: ?",
            "description: - 日本語",
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

    def test_non_string_rejects_empty_alternative(self):
        self.assertNotIn("||", NON_STRING.pattern)
        self.assertFalse(NON_STRING.pattern.startswith("|"))
        self.assertFalse(NON_STRING.pattern.endswith("|"))
        self.assertIsNone(NON_STRING.fullmatch(""))
        self.assertIsNone(NON_STRING.fullmatch("説明"))
        for bad in ["|yes", "yes|", "yes||no", ""]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                compile_non_string([bad])

    def test_rejects_duplicate_key_and_missing_block(self):
        with self.assertRaises(ValueError):
            parse_frontmatter("---\nname: a\nname: b\n---\n本文\n")
        with self.assertRaises(ValueError):
            parse_frontmatter("本文だけ\n")


if __name__ == "__main__":
    unittest.main()
