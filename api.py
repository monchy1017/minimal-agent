"""
api.py - FastAPI アプリケーション

REST APIのエントリーポイント。
各エンドポイントとHTTPメソッドを定義します。

起動方法:
    uv run uvicorn api:app --reload

ドキュメント確認:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI, HTTPException, status

from agent import AgentState, get_agent
from schemas import AnalysisRequest, AnalysisResponse, ErrorResponse, PaperResponse

# === FastAPIアプリの初期化 ===
app = FastAPI(
    title="Paper Analysis API",
    description="""
    arXiv論文を検索・分析するAPI

    ## 機能
    - キーワードからarXiv検索クエリを自動生成
    - 関連論文を検索・収集
    - LLMによる論文分析とレポート生成

    ## REST設計
    - `POST /analyses` : 新しい分析を作成（リソースの作成）
    - `GET /` : ヘルスチェック
    """,
    version="1.0.0",
)


# === エンドポイント定義 ===


@app.get("/", tags=["Health"])
def root():
    """
    ヘルスチェック用エンドポイント

    APIが正常に動作しているか確認するために使用します。
    RESTでは、ルートパスにAPIの状態を返すエンドポイントを置くのが一般的です。
    """
    return {"status": "ok", "message": "Paper Analysis API is running"}


@app.post(
    "/analyses",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Analyses"],
    responses={
        201: {"description": "分析が正常に完了"},
        400: {"model": ErrorResponse, "description": "リクエストが不正"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
)
def create_analysis(request: AnalysisRequest):
    """
    新しい論文分析を実行

    ## RESTの観点
    - **POST** を使用: 新しいリソース（分析結果）を「作成」するため
    - **201 Created** を返す: リソースが正常に作成されたことを示す
    - **リクエストボディ**: JSON形式でキーワードを送信
    - **レスポンス**: 作成されたリソース（分析結果）を返す

    ## 処理フロー
    1. キーワードを受け取る
    2. arXiv検索クエリを生成
    3. 論文を検索
    4. LLMで分析
    5. レポートを生成して返す
    """
    try:
        # エージェントを取得
        agent = get_agent()

        # 初期状態を作成
        initial_state: AgentState = {
            "keyword": request.keyword,
            "queries": [],
            "core_papers": None,
            "analysis": None,
            "web_search_logs": None,
            "report_markdown": None,
        }

        # エージェントを実行
        print(f"\n{'=' * 50}")
        print(f"Starting analysis for: {request.keyword}")
        print(f"{'=' * 50}")

        result = agent.invoke(initial_state)

        # レスポンスを構築
        papers = result.get("core_papers", [])
        return AnalysisResponse(
            keyword=result["keyword"],
            queries=result.get("queries", []),
            papers_count=len(papers),
            papers=[
                PaperResponse(title=p["title"], summary=p["summary"], url=p["url"])
                for p in papers
            ],
            report_markdown=result.get("report_markdown", ""),
            web_search_logs=result.get("web_search_logs", []),
        )

    except ValueError as e:
        # 論文が見つからない等のビジネスロジックエラー
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # 予期せぬエラー
        print(f"Error during analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析中にエラーが発生しました: {str(e)}",
        )


# === 開発用：直接実行時の起動 ===
if __name__ == "__main__":
    import uvicorn

    # 開発サーバーを起動
    # --reload: コード変更時に自動再起動
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
