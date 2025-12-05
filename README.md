# 📘 Minimal Paper Agent
自律的に論文を調査・分析し、レポートをObsidianに保存するエージェント

## 概要
指定されたキーワードに基づき、arXivから論文を検索し、LLM (gpt-4o-mini) が内容を深く分析します。 

特徴は、分析中に不明な専門用語や実装の詳細が必要になった場合、エージェントが自律的にWeb検索 (DuckDuckGo) を行い、知識を補完しながら解説を作成する点です。

## 🚀 ワークフロー
LangGraphを用いた自律的なパイプライン処理により、深い分析を実現しています。

```mermaid
    %% ノードの定義
    Start((Start))
    GenQuery[Generate Queries<br><sub>ユーザー入力を学術クエリに変換</sub>]
    FindPapers[Find Papers<br><sub>arXivで論文を取得</sub>]
    
    subgraph Analysis_Phase [分析フェーズ]
        direction TB
        Agent{Agentic Analysis<br><sub>論文を読み込み</sub>}
        Tool[🛠️ Web Search<br><sub>DuckDuckGo</sub>]
    end
    
    Compile[Compile Report<br><sub>レポート作成・保存</sub>]
    End((End))

    %% フローの定義
    Start --> GenQuery
    GenQuery --> FindPapers
    FindPapers --> Agent
    
    %% ReActループの表現
    Agent -- "知らない用語がある..." --> Tool
    Tool -- "検索結果" --> Agent
    
    Agent -- "解説完了" --> Compile
    Compile --> End

    %% スタイル
    style Agent fill:#f9f,stroke:#333,stroke-width:2px
    style Tool fill:#bbf,stroke:#333,stroke-width:1px
    style Start fill:#cfc,stroke:#333
    style End fill:#cfc,stroke:#333
```


## ✨ 主な機能
- Query Transformation：
入力された日本語のキーワードを、arXiv検索に最適な**英語の学術用語（3パターン）**に自動変換し、検索漏れを防ぎます。

- 自律的な深掘り分析 (Agentic Analysis)：
論文要約を読む際、未知の専門用語や具体的な手法名が登場すると、自らWeb検索ツールを呼び出し、背景知識を補完してから解説を書きます。

- マルチ情報源の統合
  - arXiv: 最新の学術論文
  - DuckDuckGo: 最新のWeb情報、GitHub実装、技術ブログ

- ナレッジベース連携：
生成されたレポートはObsidian (iCloud) にも自動保存され、個人の知識ベースとして蓄積されます。


## 🛠️ 技術スタック
Language: Python 3.10+

Orchestration: LangGraph

LLM: OpenAI API (gpt-4o-mini)

Search: arxiv API, duckduckgo-search

CLI: Typer

Package Manager: uv

## 📦 How To Use
パッケージマネージャーには uv を推奨しています。

1. リポジトリのクローン

```bash
git clone <repository-url>
cd minimal-agent
```

2. 環境変数の設定：.env ファイルを作成し、OpenAI APIキーを設定してください。

```bash
echo 'OPENAI_API_KEY="sk-your-api-key-here"' > .env
```

3. 依存関係のインストール

```
uv venv
uv pip install -p pyproject.toml
# または直接インストールする場合:
# uv pip install langgraph langchain-openai arxiv typer python-dotenv langchain-community duckduckgo-search
```

4. Obsidianパスの設定 (Optional)：main.py 内の obsidian_path 変数を、ご自身の環境に合わせて修正してください。


## 💻 使い方
コマンドライン引数として「調査したいテーマ」を渡すだけです。日本語OK！

```bash
uv run python main.py "例<Mixture of Experts>"
```

### 日本語でもOK (自動翻訳されます)
```bash
uv run python main.py "LLMの推論高速化"
```

## 📄 出力レポート例

生成されるMarkdownレポートには以下の情報が含まれます。

- 実行された検索クエリ一覧: arXiv検索に使われたキーワード
- Web検索ログ: エージェントが分析中に何を調べたかの履歴
- 論文詳細:
- タイトル / URL
- 核心的な貢献 (Web検索で補完された詳細解説)