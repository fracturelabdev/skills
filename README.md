# skills

fracturelab が公開する Claude Code 用 Skill のプラグイン集です。
テーマごとにプラグインを分けているので、必要なものだけを入れられます。

## 使い方

```sh
claude plugin marketplace add fracturelabdev/skills
claude plugin install <plugin>@fracturelab
```

例（`tickets` を入れる場合）:

```sh
claude plugin marketplace add fracturelabdev/skills
claude plugin install tickets@fracturelab
```

セッション内では `/plugin marketplace add fracturelabdev/skills` でも登録できます。
Skill は `/<plugin>:<skill>` の形で呼び出します。

更新を取り込むときは `claude plugin marketplace update fracturelab` を実行します。

## プラグイン

| プラグイン | 内容 |
|---|---|
| [`tickets`](plugins/tickets) | fracturelab 流の GitHub Issue / PR の書き方と、ドキュメントの置き場所の案内（`/tickets:issue` `/tickets:pr` `/tickets:docs`） |

## 方針

- 日本語で書きます
- 個人の環境（特定のパス・アカウント・認証情報）に依存する Skill は載せません
- 決めたことは [`DECISIONS.md`](DECISIONS.md) に残します

## ライセンス

[MIT](LICENSE)
