"""
schemas.py - リクエスト/レスポンスのデータ構造を定義

REST APIでは「リソースの表現（Representation）」が重要。
Pydanticを使って、APIでやり取りするデータの形を明確に定義します。
"""
from pydantic import BaseModel, Field
from typing import List


# === リクエスト（クライアント → サーバー） ===

class AnalysisRequest(BaseModel):
    """分析リクエスト: クライアントが送信するデータ"""
    keyword: str = Field(
        ...,  # 必須フィールド
        min_length=1,
        max_length=200,
        description="分析したいトピックやキーワード",
        examples=["LLM efficiency", "transformer attention mechanism"]
    )


# === レスポンス（サーバー → クライアント） ===

class PaperResponse(BaseModel):
    """論文情報のレスポンス"""
    title: str
    summary: str
    url: str


class AnalysisResponse(BaseModel):
    """分析結果のレスポンス: サーバーが返すデータ"""
    keyword: str = Field(description="入力されたキーワード")
    queries: List[str] = Field(description="生成された検索クエリ")
    papers_count: int = Field(description="見つかった論文数")
    papers: List[PaperResponse] = Field(description="論文一覧")
    report_markdown: str = Field(description="生成されたレポート（Markdown形式）")
    web_search_logs: List[str] = Field(
        default=[],
        description="実行されたWeb検索のログ"
    )


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    detail: str = Field(description="エラーの詳細メッセージ")
