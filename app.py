"""
app.py - Streamlit フロントエンド

REST APIを呼び出すシンプルなGUIです。
APIとフロントエンドが分離していることで、REST設計の恩恵を確認できます。

起動方法:
    1. まずAPIサーバーを起動: uv run uvicorn api:app --reload
    2. 別ターミナルでStreamlit起動: uv run streamlit run app.py
"""

import requests
import streamlit as st

# === 設定 ===
API_BASE_URL = "http://localhost:8000"

# === ページ設定 ===
st.set_page_config(page_title="Paper Analysis", page_icon="📚", layout="wide")

# === ヘッダー ===
st.title("📚 論文分析ツール")
st.markdown("""
arXivの論文を検索・分析してレポートを生成します。

""")

st.divider()


# === API状態確認 ===
def check_api_health():
    """APIのヘルスチェック (GET /)"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


# サイドバーにAPI状態を表示
with st.sidebar:
    st.header("API Status")
    if check_api_health():
        st.success("API: 接続OK")
    else:
        st.error("API: 未接続")
        st.markdown("""
        APIサーバーを起動してください:
        ```bash
        uv run uvicorn api:app --reload
        ```
        """)

    st.divider()
    st.markdown("""
    ### エンドポイント
    - `GET /` - ヘルスチェック
    - `POST /analyses` - 分析実行

    ### ドキュメント
    - [Swagger UI](http://localhost:8000/docs)
    - [ReDoc](http://localhost:8000/redoc)
    """)

# === メインコンテンツ ===
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("入力")

    # キーワード入力
    keyword = st.text_input(
        "検索キーワード",
        placeholder="例: transformer attention mechanism",
        help="日本語でも英語でもOK。英語に自動変換されます。",
    )

    # 分析実行ボタン
    analyze_button = st.button(
        "分析を実行", type="primary", disabled=not keyword, use_container_width=True
    )

with col2:
    st.subheader("結果")

    if analyze_button and keyword:
        # API呼び出し
        with st.spinner("分析中... (数分かかる場合があります)"):
            try:
                # POST /analyses にリクエスト
                response = requests.post(
                    f"{API_BASE_URL}/analyses",
                    json={"keyword": keyword},
                    timeout=300,  # 5分タイムアウト
                )

                if response.status_code == 201:
                    data = response.json()

                    # 成功メッセージ
                    st.success(
                        f"分析完了! {data['papers_count']}件の論文を分析しました"
                    )

                    # 生成されたクエリ
                    st.markdown("**生成された検索クエリ:**")
                    for q in data.get("queries", []):
                        st.code(q)

                    # Web検索ログ
                    if data.get("web_search_logs"):
                        with st.expander("実行されたWeb検索"):
                            for log in data["web_search_logs"]:
                                st.write(f"- {log}")

                    # タブで結果を表示
                    tab1, tab2, tab3 = st.tabs(["レポート", "論文一覧", "Raw JSON"])

                    with tab1:
                        st.markdown(data.get("report_markdown", "レポートなし"))

                    with tab2:
                        for i, paper in enumerate(data.get("papers", []), 1):
                            with st.expander(f"{i}. {paper['title'][:60]}..."):
                                st.markdown(f"**URL:** {paper['url']}")
                                st.markdown("**概要:**")
                                st.write(paper["summary"][:500] + "...")

                    with tab3:
                        st.json(data)

                elif response.status_code == 400:
                    st.error(
                        f"リクエストエラー: {response.json().get('detail', '不明なエラー')}"
                    )
                else:
                    st.error(f"エラー (HTTP {response.status_code}): {response.text}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "APIサーバーに接続できません。サーバーが起動しているか確認してください。"
                )
            except requests.exceptions.Timeout:
                st.error("タイムアウトしました。分析に時間がかかりすぎています。")
            except Exception as e:
                st.error(f"予期せぬエラー: {e}")

    elif not keyword:
        st.info("キーワードを入力して「分析を実行」をクリックしてください")
