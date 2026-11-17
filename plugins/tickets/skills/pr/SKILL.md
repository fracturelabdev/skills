---
name: pr
description: Pull Request を fracturelab 流で書く。「PR 本文を書いて」「PR を出したい」「対応 Issue の書き方」と頼まれたときに使う。branch の type、commit と PR タイトルの type と scope、本文の見出し、対応 Issue への Closes の書き方を案内する。
---

# PR の書き方

正本は [fracturelabdev/.github の CONTRIBUTING](https://github.com/fracturelabdev/.github/blob/main/.github/CONTRIBUTING.md) と、同じ場所の PR テンプレート。この skill は開かなくても書けるようにまとめた案内で、食い違いがあれば CONTRIBUTING を優先する。

## 基本

- 1 Issue = 1 branch = 1 PR。複数の Issue を 1 つの PR で閉じない
- 本文は日本語。branch 名、commit の type、scope は英語
- `[アイデア]` の Issue には PR を紐付けない。着手するときは `[改修]` を起票し直す
- `[作業]` の PR 紐付けは任意。紐付けるときは下の形式に従う

## type

branch 名・commit 件名・PR タイトルで共通。次の 6 つだけ。

| type | 用途 |
|---|---|
| `feat` | 機能追加・仕様変更 |
| `fix` | 不具合修正 |
| `refactor` | 挙動を変えないコード整理 |
| `docs` | ドキュメントのみ |
| `test` | テストのみ |
| `chore` | 設定・依存更新・雑務 |

## branch

```
<type>/<issue番号>-<英語の短い説明>
```

- scope は付けない。説明は小文字・ハイフン区切り・3 語以内
- 自由記述は入れない。Issue 番号のない branch は作らない
- 例: `fix/123-login-timeout`、`feat/456-export-csv`、`docs/78-api-guide`

## commit と PR タイトル

```
<type>(<scope>): <要約> (#<issue番号>)
```

- 件名は 50 字以内。文末に句点を付けない
- `scope` は変更対象の英語名。閉じた一覧は無い。例は `api` `auth` `ui` `db`。省略して `<type>: <要約> (#<issue番号>)` でもよい
- commit の本文は任意で 3 行以内。なぜその commit が必要かが diff から読めないときだけ書く
- PR タイトルは squash merge 後の履歴になる。commit 件名と同じ形式で書く
- 例: `fix(auth): セッション更新時のタイムアウト判定を修正 (#123)`
- 例: `docs: API の手順を追記 (#78)`

## PR 本文

テンプレートの見出しを消さない・並べ替えない。見出しは次のとおり。

1. `## 対応 Issue`
2. `## 変更概要`
3. `## 完了条件の充足`
4. `## 検証証跡`
5. `## レビュー観点`
6. `## 補足（任意・200字以内）`

`## 検証証跡` の下には、テンプレートの `### CI` と `### 手動実行（CI 未整備 or CI 外の確認）` を残す。

## 対応 Issue

`Closes #N` は、見出し `## 対応 Issue` に 1 件だけ書く。例: `Closes #123`。

- その Issue の完了条件を満たす PR は 1 本にする。マージで Issue が閉じる
- 完了条件に未 ✓ があるときも、同じ PR の対応 Issue は `Closes #N` のまま Draft で出し、満たしてから Ready にする。部分対応をマージして続きを別 PR に回さない。分けたいなら先に Issue を分割する
- `[アイデア]` には書かない。PR を紐付けない
- `Refs #N` は CONTRIBUTING に無い。対応 Issue にも、ほかの見出しにも書かない

## 各欄の書き方

- 変更概要: 何を変えたかを 3 点以内。理由は書かない
- 完了条件の充足: Issue の完了条件をそのまま転記し、満たしたものに ✓ を付ける
- 検証証跡: CI の URL、または実行コマンドと結果。どちらかは必ず埋める。空欄、または「テストした」という文章だけは不可
- レビュー観点: 見てほしい箇所を `ファイル名:行` または関数名で、3 点以内
- 補足: 迷った判断・既知の制約・後続 Issue。200 字以内。任意
- 理由や背景は PR に書かない。Issue に書く

未充足の条件がある、または検証証跡が埋まっていないときは Draft で出す。
