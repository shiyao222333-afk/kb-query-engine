"""
测试重排序功能
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reranker import rerank_results, rerank_results_simple

# 模拟搜索结果
mock_results = [
    {
        "id": "1",
        "score": 0.95,
        "payload": {
            "text": "齿轮模数选择需要考虑载荷、转速和材料因素。",
            "title": "齿轮设计手册",
            "source": "gear_design.pdf"
        }
    },
    {
        "id": "2",
        "score": 0.90,
        "payload": {
            "text": "模数是齿轮的基本参数，单位为毫米。",
            "title": "机械原理",
            "source": "mech_principle.pdf"
        }
    },
    {
        "id": "3",
        "score": 0.85,
        "payload": {
            "text": "人工智能在工业设计中的应用越来越广泛。",
            "title": "AI与设计",
            "source": "ai_design.pdf"
        }
    }
]

query = "齿轮模数怎么选"

print("=" * 60)
print("测试 1: 使用 Ollama 重排序")
print("=" * 60)
print(f"查询: {query}")
print(f"原始结果数: {len(mock_results)}")
print()

try:
    reranked = rerank_results(query, mock_results, top_n=3)
    print("✅ 重排序成功！")
    print()
    print("重排序后的结果:")
    for i, r in enumerate(reranked):
        text = r["payload"]["text"][:50]
        rerank_score = r.get("rerank_score", "N/A")
        print(f"  {i+1}. [{rerank_score:.4f}] {text}...")
    print()
except Exception as e:
    print(f"❌ 重排序失败: {e}")
    print()

print("=" * 60)
print("测试 2: 模拟重排序（不依赖 Ollama）")
print("=" * 60)

reranked_mock = rerank_results_simple(query, mock_results, top_n=3)
print("✅ 模拟重排序成功！")
print()
print("模拟重排序后的结果:")
for i, r in enumerate(reranked_mock):
    text = r["payload"]["text"][:50]
    rerank_score = r.get("rerank_score", "N/A")
    print(f"  {i+1}. [{rerank_score:.4f}] {text}...")

print()
print("=" * 60)
print("测试完成！")
print("=" * 60)
