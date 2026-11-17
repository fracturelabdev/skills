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
- `[作業]` の PR 紐付けは任意。任意なのは branch も commit も PR も作らない場合だけである。PR を出すときはほかの型と同じく Issue を 1 件に紐付ける。出さないときの各欄は「`[作業]` で紐付けないとき」に従う

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
- 自由記述は入れない。Issue 番号のない branch は作らない。紐付けない `[作業]` では branch も commit も PR も作らない
- 例: `fix/123-login-timeout`、`feat/456-export-csv`、`docs/78-api-guide`

## commit と PR タイトル

```
<type>(<scope>): <要約> (#<issue番号>)
```

- 件名は 50 字以内。文末に句点を付けない
- `scope` は変更対象の英語名。閉じた一覧は無い。例は `api` `auth` `ui` `db`。省略して `<type>: <要約> (#<issue番号>)` でもよい
- commit の本文は任意で 3 行以内。なぜその commit が必要かが diff から読めないときだけ書く
- マージは squash のみ。merge commit と rebase merge は使わない。squash のメッセージは PR タイトルをそのまま使う
- PR タイトルは squash 後の履歴になる。commit 件名と同じ形式で書く
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

PR を出すときは、`Closes #N` を見出し `## 対応 Issue` に 1 件だけ書く。見出しは消さない。例: `Closes #123`。紐付けない `[作業]` は PR を出さないので、この見出しは作らない。

- その Issue の完了条件を満たす PR は 1 本にする。マージで Issue が閉じる
- 完了条件に未 ✓ があるときも、同じ PR の対応 Issue は `Closes #N` のまま Draft で出し、満たしてから Ready にする。部分対応をマージして続きを別 PR に回さない。分けたいなら先に Issue を分割する
- `[アイデア]` には書かない。PR を紐付けない
- `Refs #N` は CONTRIBUTING に無い。対応 Issue にも、ほかの見出しにも書かない

## `[作業]` で紐付けないとき

CONTRIBUTING は `[作業]` の PR 紐付けを任意としている。branch・commit・PR タイトルは Issue 番号が必須で、差し戻し基準は、対応 Issue が無い PR と、branch 名・タイトルが形式に合わない PR を Draft に戻す。`.github` の PR format check も、`## 対応 Issue` に `#` と番号が無い、またはタイトルが `(#N)` で終わらないと失敗する。番号の無い `[作業]` を PR にすると、この検査で失敗する。

紐付けないときは、branch も commit も PR も作らない。`(#N)` を省いた件名や type を変えた件名も、件名の形式を問わず作らない。番号の無い branch と、見出しを空にした PR も作らない。PR を出す `[作業]` は、ほかの型と同じく `Closes #N` を 1 件だけ書く。

| 欄 | 紐付けないとき | 紐付けるとき |
|---|---|---|
| branch 名 | 作らない | `<type>/<issue番号>-<英語の短い説明>` |
| commit | 作らない。件名の形式を変えても作らない | `<type>(<scope>): <要約> (#N)` |
| PR タイトル | 作らない（PR を出さない） | commit 件名と同じ形式 |
| `## 対応 Issue` | 作らない | 消さず、`Closes #N` を 1 件だけ書く |
| `Refs #N` | 書かない | 書かない |

## 各欄の書き方

- 変更概要: 何を変えたかを 3 点以内。理由は書かない
- 完了条件の充足: Issue の完了条件をそのまま転記し、満たしたものに ✓ を付ける
- 検証証跡: CI の URL、または実行コマンドと結果。Ready ではどちらかを必ず埋める。空欄、または「テストした」という文章だけは Ready にしない。空欄が許されるのは Draft のあいだだけである
- レビュー観点: 見てほしい箇所を `ファイル名:行` または関数名で、3 点以内
- 補足: 迷った判断・既知の制約・後続 Issue。200 字以内。任意
- 理由や背景は PR に書かない。Issue に書く

完了条件に未 ✓ があるとき、または検証証跡が空のときは Draft で出す。Draft のあいだは検証証跡が空でもよい。未 ✓ を消し、検証証跡を埋めてから Ready にする。Ready の検証証跡が空、または文章だけなら差し戻しになる。
