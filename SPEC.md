# Minimal Paper Agent - 仕様書

## 1. プロジェクト概要

キーワードを入力するだけで、arXiv上の関連論文を自動検索・分析し、Markdownレポートを生成するAIエージェントシステム。

日本語キーワード入力にも対応しており、LLMが自動的に適切な英語学術クエリへ変換する。分析中に未知の専門用語を検出した場合、エージェントが自律的にWeb検索（DuckDuckGo）を行い補足情報を収集する（ReActパターン）。

---

## 2. システムアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                   Client (Browser)                  │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP Request
┌───────────────────────▼─────────────────────────────┐
│           Frontend  (Streamlit / app.py)             │
│   - キーワード入力UI                                  │
│   - 分析結果・レポート表示                            │
└───────────────────────┬─────────────────────────────┘
                        │ POST /analyses (JSON)
┌───────────────────────▼─────────────────────────────┐
│              API Server (FastAPI / api.py)           │
│   - GET  /         : ヘルスチェック                   │
│   - POST /analyses : 分析実行                        │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              Agent Pipeline (agent.py)               │
│   LangGraph による 4ノード構成                        │
│                                                     │
│  [generate_queries] → [find_core_papers]             │
│       → [analyze_paper] → [compile_report]          │
└──────────┬────────────────────────┬─────────────────┘
           │                        │
┌──────────▼──────────┐  ┌──────────▼──────────────┐
│    arXiv API        │  │  OpenAI API (gpt-4o-mini)│
│  (論文検索)          │  │  (クエリ生成 / 論文分析)  │
└─────────────────────┘  └──────────┬───────────────┘
                                    │ Tool Call (必要時)
                         ┌──────────▼──────────────┐
                         │  DuckDuckGo Search       │
                         │  (専門用語・実装調査)     │
                         └─────────────────────────┘
```

---

## 3. コンポーネント詳細

### 3.1 エントリーポイント

| ファイル | 役割 | 起動方法 |
|----------|------|----------|
| `main.py` | CLIエントリーポイント（ローカル実行用） | `uv run python main.py "キーワード"` |
| `api.py` | FastAPI REST APIサーバー | `uv run uvicorn api:app --reload` |
| `app.py` | StreamlitフロントエンドUI | `uv run streamlit run app.py` |

### 3.2 コアモジュール

#### `agent.py` - LangGraph パイプライン

LangGraphの `StateGraph` で構成される4ノードの処理パイプライン。

| ノード名 | 関数 | 処理内容 |
|----------|------|----------|
| `generate_queries` | `generate_queries()` | ユーザー入力をarXiv向け英語クエリ3件に変換 |
| `find_core_papers` | `find_core_papers()` | 各クエリでarXiv検索し、最大10件の論文を収集 |
| `analyze_paper` | `analyze_paper_with_llm()` | ReActエージェントで各論文を分析（必要時Web検索） |
| `compile_report` | `compile_report()` | 分析結果をMarkdownレポートとしてまとめる |

**状態管理 (`AgentState`)**:

```python
class AgentState(TypedDict):
    keyword: str                        # 入力キーワード
    queries: List[str]                  # 生成されたarXivクエリ
    core_papers: Optional[List[PaperInfo]]  # 取得した論文リスト
    analysis: Optional[List[str]]       # 各論文の分析結果
    web_search_logs: Optional[List[str]]    # Web検索ログ
    report_markdown: Optional[str]      # 最終レポート(Markdown)
```

#### `schemas.py` - Pydantic スキーマ

| クラス | 種別 | 説明 |
|--------|------|------|
| `AnalysisRequest` | リクエスト | キーワード（1〜200文字、必須） |
| `PaperResponse` | レスポンス | 論文情報（title / summary / url） |
| `AnalysisResponse` | レスポンス | 分析結果全体（keyword / queries / papers / report） |
| `ErrorResponse` | エラー | エラー詳細メッセージ |

---

## 4. API仕様

### ベースURL
```
http://localhost:8000
```

### エンドポイント一覧

#### `GET /`
ヘルスチェック

**レスポンス (200 OK)**:
```json
{
  "status": "ok",
  "message": "Paper Analysis API is running"
}
```

---

#### `POST /analyses`
論文分析の実行

**リクエストボディ**:
```json
{
  "keyword": "LLMの推論高速化"
}
```

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `keyword` | string | ✅ | 分析キーワード（1〜200文字） |

**レスポンス (201 Created)**:
```json
{
  "keyword": "LLMの推論高速化",
  "queries": [
    "LLM inference acceleration",
    "Large Language Model optimization",
    "Speculative decoding"
  ],
  "papers_count": 9,
  "papers": [
    {
      "title": "...",
      "summary": "...",
      "url": "https://arxiv.org/pdf/xxxx.xxxxx"
    }
  ],
  "report_markdown": "# 論文分析レポート: ...",
  "web_search_logs": [
    "speculative decoding GitHub (Context: ...)"
  ]
}
```

**エラーレスポンス**:

| ステータスコード | 条件 |
|-----------------|------|
| `400 Bad Request` | 論文が1件も見つからなかった場合 |
| `500 Internal Server Error` | 予期せぬエラー（API通信失敗など） |

---

## 5. フロントエンド仕様 (Streamlit)

| 要素 | 説明 |
|------|------|
| キーワード入力欄 | テキスト入力（日本語・英語対応） |
| 分析実行ボタン | キーワード未入力時は無効化 |
| サイドバー | API接続状態、エンドポイント一覧、Swaggerリンク |
| 結果タブ①「レポート」 | Markdownレポートをレンダリング表示 |
| 結果タブ②「論文一覧」 | 論文ごとのexpander（タイトル / URL / 概要500文字） |
| 結果タブ③「Raw JSON」 | APIレスポンス全体をJSON表示 |
| API接続URL | 環境変数 `API_BASE_URL`（デフォルト: `http://localhost:8000`） |

---

## 6. 依存ライブラリ

| ライブラリ | 用途 |
|------------|------|
| `langgraph` | エージェントパイプライン構築 |
| `langchain-openai` | OpenAI API接続 |
| `langchain-community` | DuckDuckGo検索ツール |
| `arxiv` | arXiv論文検索 |
| `fastapi` | REST APIフレームワーク |
| `uvicorn[standard]` | ASGIサーバー |
| `streamlit` | WebフロントエンドUI |
| `requests` | StreamlitからAPIへのHTTPリクエスト |
| `python-dotenv` | `.env`ファイル読み込み |
| `typer` | CLIインターフェース構築 |
| `ddgs` | DuckDuckGo検索バックエンド |

パッケージ管理: **uv**（`pyproject.toml` + `uv.lock`）

---

## 7. 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI APIキー |
| `OBSIDIAN_PATH` | CLIのみ | CLIモードでのレポート保存先パス |
| `API_BASE_URL` | フロントエンドのみ | フロントエンドが接続するAPI URL（デフォルト: `http://localhost:8000`） |

---

## 8. 処理フロー詳細

```
ユーザー入力 (keyword)
    │
    ▼
[generate_queries]
    GPT-4o-mini でarXiv向け英語クエリを3件生成
    日本語 → 学術的英語キーワードへ変換
    │
    ▼
[find_core_papers]
    各クエリでarXiv検索 (最大3件/クエリ)
    重複除外して最大10件を収集
    │
    ▼
[analyze_paper_with_llm]  ← ReActループ
    GPT-4o-mini + web_search ツール
    各論文ごとに abstract を読み、日本語で約300字の要約を生成
    未知の専門用語・実装状況があればDuckDuckGoで補足検索
    │
    ▼
[compile_report]
    Markdownレポート生成
    - 検索クエリ一覧
    - Web検索ログ
    - 論文ごとの分析（タイトル / URL / Core Contribution）
    │
    ▼
 APIレスポンス / ファイル保存 (CLIモード)
```

---

## 9. ローカル開発手順

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd minimal-agent

# 2. 仮想環境作成 & 依存インストール
uv venv
uv pip install -r pyproject.toml

# 3. 環境変数設定
echo 'OPENAI_API_KEY="sk-..."' > .env

# 4. APIサーバー起動
uv run uvicorn api:app --reload --port 8000

# 5. フロントエンド起動（別ターミナル）
uv run streamlit run app.py

# 6. CLI実行（直接レポート生成）
uv run python main.py "軽量なLLM"
```
