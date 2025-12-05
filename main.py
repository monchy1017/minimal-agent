import typer
from agent import get_agent

app = typer.Typer()


@app.command()
def run(keyword: str):
    """
    論文分析エージェントをキーワードで実行します。
    例: uv run python main.py "軽量なLLM"
    """
    print(f"🚀 エージェントを実行します (キーワード: '{keyword}')")

    agent = get_agent()
    inputs = {"keyword": keyword}

    final_state = None

    try:
        for s in agent.stream(inputs, {"recursion_limit": 100}):
            node_name = list(s.keys())[0]
            print(f"\n[✅ ノード完了: {node_name}]")
            if node_name == "generate_queries":
                print(f"👉 Generated Queries: {s[node_name].get('queries')}")

            final_state = s

        print("\n\n" + "=" * 30)
        print("      📝 分析レポート      ")
        print("=" * 30 + "\n")

        if final_state:
            # 最後のノード（compile_report）の結果を取得
            last_node_output = list(final_state.values())[0]
            report = last_node_output.get("report_markdown")
            print(report)
        else:
            print("レポートが生成されませんでした。")

    except Exception as e:
        print(f"\n[❌ エラー発生] 処理中にエラーが発生しました: {e}")


if __name__ == "__main__":
    app()
