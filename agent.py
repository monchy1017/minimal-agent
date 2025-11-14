import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
import arxiv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage

load_dotenv()
if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEYが.envファイルに設定されていません")


class PaperInfo(TypedDict):
    """論文情報の型"""

    title: str
    summary: str
    url: str


class AgentState(TypedDict):
    """エージェント全体の記憶（状態）の型"""

    keyword: str
    core_paper: Optional[PaperInfo]
    analysis: Optional[str]
    report_markdown: Optional[str]


def find_core_paper(state: AgentState) -> AgentState:
    """ノード1: arXivで中心論文を検索する"""
    print("finding core paper...")
    keyword = state["keyword"]
    search = arxiv.Search(
        query=keyword, max_results=1, sort_by=arxiv.SortCriterion.Relevance
    )
    result = next(search.results(), None)

    if result:
        core_paper = PaperInfo(
            title=result.title, summary=result.summary, url=result.pdf_url
        )
        print(f"論文を発見: {core_paper['title']}")
        return {**state, "core_paper": core_paper}
    else:
        raise ValueError(
            f"キーワード '{keyword}' に一致する論文が見つかりませんでした。"
        )


def analyze_paper_with_llm(state: AgentState) -> AgentState:
    """ノード2: LLMで論文を分析する"""
    print("analyzing paper with llm...")
    if not state["core_paper"]:
        return state

    # gpt-4o-miniモデルを指定して初期化
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)

    paper = state["core_paper"]
    prompt = f"""
    以下の論文の要約を読み、その論文の「核心的な貢献」を200字程度で簡潔に解説してください。

    論文タイトル: {paper['title']}
    要約:
    {paper['summary']}

    核心的な貢献:
    """

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        analysis_text = response.content
        print("分析完了!")
        return {**state, "analysis": analysis_text}
    except Exception as e:
        print(f"LLMの呼び出し中にエラーが発生しました: {e}")
        return {**state, "analysis": "分析中にエラーが発生しました。"}


def compile_report(state: AgentState) -> AgentState:
    """ノード3: 最終レポートを作成する"""
    print("compiling report...")

    paper = state["core_paper"]
    analysis = state["analysis"]

    if not paper or not analysis:
        report = "# 分析レポート\n\n情報の取得に失敗しました。"
        return {**state, "report_markdown": report}

    report = f"""
    # 論文分析レポート: {state['keyword']}
    ## 1. 中心論文
    - **タイトル:** {paper['title']}
    - **URL:** {paper['url']}
    ## 2. 核心的な貢献 (by gpt-5-mini)
    {analysis}
    ## 3. 要約 (Abstract)
    {paper['summary']}
    """
    print("レポート作成完了。")
    return {**state, "report_markdown": report.strip()}


def get_agent():
    """エージェントのグラフを構築し、
    → 順番にノードをadd
    →コンパイルして返す
    """
    builder = StateGraph(AgentState)

    # ノードをグラフに追加
    builder.add_node("find_core_paper", find_core_paper)
    builder.add_node("analyze_paper", analyze_paper_with_llm)
    builder.add_node("compile_report", compile_report)

    # エッジ（ノード間の繋がり）を定義
    builder.add_edge(START, "find_core_paper")  # 開始地点
    builder.add_edge("find_core_paper", "analyze_paper")
    builder.add_edge("analyze_paper", "compile_report")
    builder.add_edge("compile_report", END)  # 終了地点
    return builder.compile()


if __name__ == "__main__":
    print("エージェントをテスト実行します...")

    agent = get_agent()

    # テスト用
    inputs = {"keyword": "Mixture of Experts"}

    for s in agent.stream(inputs, {"recursion_limit": 100}):
        node_name = list(s.keys())[0]
        print(f"\nノード '{node_name}' が完了")
        print(s[node_name])
