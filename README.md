🇬🇧 [English version](README.en.md)

# Dexter JP — 日本株の自律型リサーチエージェント

> 聞くだけで、勝手に計画を立てて、複数のデータソースを横断して、自分で検証しながらレポートまで仕上げる。

[EDINET DB](https://edinetdb.jp) + [J-Quants](https://jpx-jquants.com/) で動く、日本株特化の金融AIエージェント。
[virattt/dexter](https://github.com/virattt/dexter)（米国株版）をフォークし、日本市場向けに全面改修。

![Dexter JP Demo](docs/demo.png)

## ただのツールではない

よくある金融ツールは「スクリーニングできます」「財務データ見れます」で終わる。Dexter JPは違う。

**「ソニーと任天堂、投資先としてどちらが優れているか分析して」** と聞くと:

1. まず計画を立てる — 比較に必要な指標（収益性、成長性、財務健全性、リスク）を自分で決める
2. 複数のツールを自律的に呼び出す — 両社の財務データ、有報のリスク要因、決算短信を並列取得
3. 途中で検証する — 数字とナラティブに矛盾がないか、データが足りているか自分で判断
4. レポートを仕上げる — 比較表と結論付きの構造化された分析結果を出力

これを1回の質問で、人間が介在せずにやる。ツールを1つ呼ぶだけの「データ取得」ではなく、複数のデータソースを横断した「分析」が自動で走る。

## セットアップ

### 必要なもの

- [Bun](https://bun.sh/)
- LLM APIキー（以下のいずれか1つ）
- [EDINET DB](https://edinetdb.jp) APIキー

### 環境変数

`.env`に設定するもの:

```bash
# === 必須 ===

# LLM（いずれか1つ。複数設定してもOK、CLI上で切替可能）
OPENAI_API_KEY=sk-...          # OpenAI（デフォルト）
ANTHROPIC_API_KEY=sk-ant-...   # Claude
GOOGLE_API_KEY=...             # Gemini
XAI_API_KEY=...                # Grok
OPENROUTER_API_KEY=...         # OpenRouter（複数モデル利用可）

# 日本株データ
EDINETDB_API_KEY=edb_...       # edinetdb.jp で取得（無料枠あり）

# === オプション ===

# 株価データ（設定すると get_stock_price ツールが有効化）
JQUANTS_API_KEY=...            # jpx-jquants.com で取得（無料、期限なし）

# Web検索（設定すると web_search ツールが有効化。優先順: Exa → Perplexity → Tavily）
EXASEARCH_API_KEY=...
PERPLEXITY_API_KEY=...
TAVILY_API_KEY=...

# X/Twitter検索
X_BEARER_TOKEN=...

# ローカルLLM
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### インストール & 起動

```bash
git clone https://github.com/edinetdb/dexter-jp.git
cd dexter-jp
bun install
cp env.example .env  # 編集してAPIキーを設定
bun run start
```

## 使い方の例

### 自律的な分析（エージェントの真価）

複雑な問いを投げると、Dexterが自分で計画を立て、複数のデータソースを横断し、レポートを仕上げる:

```
トヨタの競争力を総合分析して。財務データ、有報のリスク要因、最新決算を踏まえてレポートにまとめて

ソニーと任天堂、投資先としてどちらが優れているか。財務健全性・収益性・成長性・リスクを比較して結論を出して

高ROE・高配当の割安銘柄を探して、トップ3の財務健全性と事業リスクを深掘り分析して

キーエンスのDCFバリュエーションをして。現在の株価水準が割高か割安か判断して
```

### シンプルな質問もOK

```
トヨタの直近5年の財務推移を見せて

ROE15%以上、自己資本比率50%以上の企業をスクリーニングして

任天堂の有報のリスク要因を読んで

配当利回り4%以上の高配当銘柄を探して
```

### 英語でも動く

```
Analyze Toyota's competitiveness. Cover financials, risk factors from the annual report, and latest earnings.

Compare Sony vs Nintendo as investment targets with a final recommendation.
```

## アーキテクチャ

```
ユーザーの質問
    ↓
エージェントループ（LangChain）
    ↓ 計画 → ツール選択 → 実行 → 検証 → 繰り返し
    ↓
┌─────────────────────────────────────────┐
│  get_financials（メタツール）             │
│    → get_financial_statements           │
│    → get_company_info                   │
│    → get_key_ratios                     │
│    → get_analysis                       │
│    → get_earnings                       │
├─────────────────────────────────────────┤
│  read_filings                           │
│    → text-blocks（有報テキスト）          │
│    → shareholders（大量保有報告書）       │
├─────────────────────────────────────────┤
│  company_screener（100+ 指標）           │
├─────────────────────────────────────────┤
│  get_stock_price（J-Quants V2）          │
├─────────────────────────────────────────┤
│  web_search / browser / skills          │
└─────────────────────────────────────────┘
    ↓
構造化されたレポート出力
```

### メタツールの仕組み

`get_financials`は単なるAPIラッパーではない。内部にLLMを持つ**ルーティングエージェント**:

1. ユーザーの自然言語クエリを受け取る
2. 内部LLMがどのサブツールを呼ぶべきか判断
3. 複数サブツールを並列実行
4. 結果を統合して返す

「ソニーとトヨタの利益率を比較して」→ 内部で4つのAPI呼び出しが自動で走る。

### スキルシステム

複雑な多段階ワークフローは`SKILL.md`で定義。DCFバリュエーションスキルを内蔵:
- 日本国債利回りベースのWACC計算
- 東証PBR1倍割れ問題の文脈
- 円建て分析

### メモリ

セッション間で記憶を保持。投資方針、ポートフォリオ情報、過去の分析結果を覚える。

### 対応LLM

`/model`コマンドでCLI上から切替可能:

- OpenAI（GPT-4o, GPT-4o-mini 等）
- Anthropic（Claude）
- Google（Gemini）
- xAI（Grok）
- OpenRouter
- Ollama（ローカルLLM）

### メッセージング連携

CLIだけでなく、Slack・Discord経由でも使える。`bun run gateway` で起動:

| チャネル | 方式 | 公開URL | 環境変数 |
|---------|------|---------|---------|
| **Slack** | Socket Mode (WebSocket) | 不要 | `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` |
| **Discord** | Gateway (WebSocket) | 不要 | `DISCORD_BOT_TOKEN` |
| **LINE** | Webhook (HTTP) | 必要 | `LINE_CHANNEL_SECRET` + `LINE_CHANNEL_ACCESS_TOKEN` |
| WhatsApp | Baileys (WebSocket) | 不要 | QRコードでログイン |

設定された環境変数に応じて、対応するチャネルだけが起動する。複数チャネル同時稼働可能。

#### Slack Bot セットアップ

1. [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → From scratch
2. **Socket Mode** → Enable → App-Level Token を生成（`xapp-`で始まるトークン）
3. **OAuth & Permissions** → Bot Token Scopes に追加:
   - `chat:write`, `im:history`, `im:read`, `app_mentions:read`
4. **Event Subscriptions** → Enable Events → Subscribe to bot events:
   - `message.im`（DM受信）, `app_mention`（メンション受信）
5. **App Home** → Messages Tab を ON → 「Allow users to send Slash commands and messages from the messages tab」にチェック
6. **Install to Workspace** → Bot Token（`xoxb-`で始まる）をコピー
7. `.env` に設定:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   ```

サーバー内ではスレッド返信、DMでは直接返信。

#### Discord Bot セットアップ

1. [discord.com/developers/applications](https://discord.com/developers/applications) → **New Application**
2. **Bot** → Reset Token → Bot Token をコピー
3. **Bot** → Privileged Gateway Intents → **Message Content Intent** を ON
4. **OAuth2** → URL Generator:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Send Messages in Threads`
5. 生成されたURLをブラウザで開いてサーバーに招待
6. `.env` に設定:
   ```bash
   DISCORD_BOT_TOKEN=MTQ4...
   ```

サーバー内では `@Bot名` メンションでスレッド返信、DMでは直接返信。

#### 起動

```bash
bun run gateway    # 設定済みの全チャネルが同時に起動
```

## データソース

| ソース | 内容 | 必須？ |
|--------|------|--------|
| [EDINET DB](https://edinetdb.jp) | 財務データ、有報テキスト、スクリーニング、AI分析（~3,800社） | 必須 |
| [J-Quants](https://jpx-jquants.com/) | 株価OHLC（東証公式） | オプション |
| Web検索 | Exa / Perplexity / Tavily | オプション |

## オリジナル版（米国株）との違い

| | Original (US) | JP Version |
|---|---|---|
| データソース | Financial Datasets API | EDINET DB API |
| 市場 | 米国株 | 日本株（~3,800社） |
| 開示書類 | SEC 10-K/10-Q/8-K | 有価証券報告書 (EDINET) |
| 決算 | 8-K earnings | TDNet 決算短信 |
| 株主情報 | SEC Form 4（インサイダー） | 大量保有報告書（5%超） |
| 株価 | Financial Datasets | J-Quants V2（TSE公式） |
| スクリーニング | GICS分類 | 33業種、100+指標 |
| DCF | 米国金利（~4%） | 日本国債（~1%） |
| 言語 | 英語 | 日本語 + 英語 |

## ライセンス

MIT

## クレジット

- オリジナル [Dexter](https://github.com/virattt/dexter) by [@virattt](https://github.com/virattt)
- 財務データ: [EDINET DB](https://edinetdb.jp)
- 株価データ: [J-Quants](https://jpx-jquants.com/)
