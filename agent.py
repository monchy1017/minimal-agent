import os
from typing import TypedDict, List, Optional
from dotenv import load_dotenv
import arxiv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
if os.getenv("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEYが.envファイルに設定されていません")


class PaperInfo(TypedDict):
    title: str
    summary: str
    url: str


class AgentState(TypedDict):
    keyword: str
    queries: List[str]  # [NEW] 生成された検索クエリリスト
    core_papers: Optional[List[PaperInfo]]
    analysis: Optional[List[str]]
    report_markdown: Optional[str]


def generate_queries(state: AgentState) -> AgentState:
    """ノード0: [NEW] ユーザー入力をarXiv用の英語クエリに変換する"""
    print("generating search queries...")
    keyword = state["keyword"]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # ユーザーの入力を、arXivでヒットしやすい英語の専門用語に変換させる
    prompt = f"""
    You are an expert AI researcher.
    Please generate 3 effective search queries for arXiv based on the user's input topic.
    
    Requirements:
    1. Translate to English if necessary.
    2. Use specific academic terms (e.g., "LLM efficiency" -> "Model Compression", "Quantization").
    3. Output ONLY the 3 queries, separated by newlines. No numbering or bullets.
    
    User Input: "{keyword}"
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    # 改行で分割してリスト化し、空白を除去
    queries = [q.strip() for q in response.content.split("\n") if q.strip()]

    print(f"Generated Queries: {queries}")
    return {**state, "queries": queries}


def find_core_papers(state: AgentState) -> AgentState:
    """ノード1: 生成されたクエリを使って論文を検索する"""
    print("finding core papers...")

    # 生成されたクエリがない場合は元のキーワードを使う（フォールバック）
    queries = state.get("queries", [state["keyword"]])

    client = arxiv.Client()
    all_papers: List[PaperInfo] = []
    seen_urls = set()

    # 各クエリで検索を実行
    for query in queries:
        print(f"  Search arXiv with: '{query}'")
        search = arxiv.Search(
            query=query,
            max_results=3,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        try:
            for result in client.results(search):
                if result.pdf_url not in seen_urls:
                    paper = PaperInfo(
                        title=result.title,
                        summary=result.summary,
                        url=result.pdf_url,
                    )
                    all_papers.append(paper)
                    seen_urls.add(result.pdf_url)
        except Exception as e:
            print(f"  Error searching for '{query}': {e}")
    final_papers = all_papers[:5]

    if not final_papers:
        raise ValueError(f"論文が見つかりませんでした。Queries: {queries}")

    print(f"Total {len(final_papers)} unique papers found.")
    return {**state, "core_papers": final_papers}


def analyze_paper_with_llm(state: AgentState) -> AgentState:
    """ノード2: LLMで論文を分析する"""
    print("analyzing papers with llm...")
    papers = state.get("core_papers")
    if not papers:
        return state

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    analysis_results: List[str] = []

    for i, paper in enumerate(papers):
        print(f"Analyzing ({i+1}/{len(papers)}): {paper['title'][:30]}...")
        prompt = f"""
        Read the abstract below and summarize the "Core Contribution" in Japanese (about 200 characters).
        
        Title: {paper['title']}
        Abstract:
        {paper['summary']}
        
        Core Contribution (Japanese):
        """
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            analysis_results.append(response.content)
        except Exception as e:
            print(f"Error analyzing paper {i}: {e}")
            analysis_results.append("分析中にエラーが発生しました。")

    return {**state, "analysis": analysis_results}


def compile_report(state: AgentState) -> AgentState:
    """ノード3: 最終レポートを作成する"""
    print("compiling report...")
    papers = state.get("core_papers")
    analyses = state.get("analysis")
    keyword = state["keyword"]
    queries = state.get("queries", [])

    if not papers or not analyses:
        return {**state, "report_markdown": "情報の取得に失敗しました。"}

    report = f"# 論文分析レポート\n\n"
    report += f"**入力テーマ:** {keyword}\n"
    report += f"**生成された検索クエリ:** {', '.join(queries)}\n\n"
    report += f"{len(papers)}件の論文が見つかりました。\n\n"

    for i, (paper, analysis) in enumerate(zip(papers, analyses)):
        report += f"## {i+1}. {paper['title']}\n"
        report += f"- **URL:** {paper['url']}\n"
        report += f"### 核心的な貢献\n{analysis}\n"
        report += f"### 要約 (Abstract)\n{paper['summary']}\n"
        report += "---\n"

    return {**state, "report_markdown": report.strip()}


def get_agent():
    builder = StateGraph(AgentState)

    builder.add_node("generate_queries", generate_queries)
    builder.add_node("find_core_papers", find_core_papers)
    builder.add_node("analyze_paper", analyze_paper_with_llm)
    builder.add_node("compile_report", compile_report)

    builder.add_edge(START, "generate_queries")
    builder.add_edge("generate_queries", "find_core_papers")
    builder.add_edge("find_core_papers", "analyze_paper")
    builder.add_edge("analyze_paper", "compile_report")
    builder.add_edge("compile_report", END)

    return builder.compile()


if __name__ == "__main__":
    pass
