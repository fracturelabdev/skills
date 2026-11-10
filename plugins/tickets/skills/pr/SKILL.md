---
name: pr
description: Pull Request を fracturelab 流で書く。「PR 本文を書いて」「PR を出したい」「Closes と Refs どちらか」と頼まれたときに使う。branch 名・タイトル・本文の見出し・Refs/Closes の使い分けを案内する。
---

# PR の書き方

正本は [fracturelabdev/.github の CONTRIBUTING](https://github.com/fracturelabdev/.github/blob/main/.github/CONTRIBUTING.md) と、同じ場所の PR テンプレート。この skill は開かなくても書けるようにまとめた案内で、食い違いがあれば CONTRIBUTING を優先する。

## 基本

- 1 Issue = 1 branch = 1 PR。複数の Issue を 1 つの PR で閉じない
- branch: `<type>/<issue番号>-<英語の短い説明>`。説明は小文字・ハイフン・3 語以内（例: `feat/12-add-search`）
- commit / PR タイトル: `<type>(<scope>): <要約> (#<issue番号>)`

## PR 本文

見出しと順番は次のとおり。消さない・並べ替えない。

1. 対応 Issue
2. 変更概要
3. 完了条件の充足
4. 検証証跡
5. レビュー観点
6. 補足（任意）

## Refs と Closes の使い分け

CONTRIBUTING の既定は、完全に満たしたときの `Closes #N`。

- `Closes #N`: その PR が Issue の完了条件をすべて満たし、マージで閉じるべきときだけ使う
- `Refs #N`: 部分対応・準備・関連づけだけで、自動 close すべきでないときに使う
- `[アイデア]` の Issue には PR を紐付けない
- 対応 Issue は 1 件だけ

## 各欄の書き方

- 変更概要: 何を変えたかを 3 点以内で。理由は書かない
- 完了条件の充足: Issue の完了条件をそのまま転記し、満たしたものに ✓ を付ける
- 検証証跡: コマンドと結果、または CI の URL。「テストした」という文章だけは不可
- 理由や背景は PR に書かない。Issue に書く

未充足の条件や証跡不足があるときは Draft で出す。
