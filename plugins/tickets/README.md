# tickets

fracturelab 流の GitHub Issue / PR の書き方と、ドキュメントの置き場所を案内するプラグインです。

## 入れ方

```sh
claude plugin marketplace add fracturelabdev/skills
claude plugin install tickets@fracturelab
```

呼び出しは次のとおりです。

| Skill | 呼び出し | 内容 |
|---|---|---|
| issue | `/tickets:issue` | Issue の型・タイトル・必須欄・完了条件 |
| pr | `/tickets:pr` | branch / タイトル / 本文の見出し、Refs と Closes |
| docs | `/tickets:docs` | ドキュメントの置き場所と命名 |

本文の正本は [CONTRIBUTING — git 記載規約](https://github.com/fracturelabdev/.github/blob/main/.github/CONTRIBUTING.md) です。食い違いがあれば CONTRIBUTING を優先します。
