import typer
from agent import get_agent

app = typer.Typer()


@app.command()
def run(keyword: str):
    """
    論文分析エージェントをキーワードで実行
    """
    print(f"🚀 エージェントを実行します (キーワード: '{keyword}')")

    agent = get_agent()
    inputs = {"keyword": keyword}  # AgentStateで定義したキー
    final_state = None
    try:
        for s in agent.stream(inputs, {"recursion_limit": 100}):
            node_name = list(s.keys())[0]
            print(f"\n[✅ノード完了: {node_name}]")
            print(s[node_name])
            final_state = s
        print("\n\n[レポート]")
        if final_state:
            last_node_output = list(final_state.values())[0]
            print(last_node_output.get("report_markdown"))

    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")


if __name__ == "__main__":
    app()
