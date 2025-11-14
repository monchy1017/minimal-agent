# minimal-agent

## ワークフロー

1.  **`[ START ]`**
    * `keyword` を受け取る
    * `↓`
2.  **`find_core_paper` (ノード1)**
    * arXiv APIで論文を検索
    * `↓`
3.  **`analyze_paper_with_llm` (ノード2)**
    * `gpt-4o-mini` で論文を分析
    * `↓`
4.  **`compile_report` (ノード3)**
    * Markdownレポートを作成
    * `↓`
5.  **`[ END ]`**
    * 最終レポートを出力