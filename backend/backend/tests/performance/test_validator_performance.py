"""性能测试：验证器性能"""
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.services.code_validator import CodeValidator


def test_validator_performance():
    """测试CodeValidator的性能"""
    validator = CodeValidator()

    # 测试不同长度内容的验证时间
    test_cases = [
        ("短内容（100字符）", "a" * 100),
        ("中等内容（1000字符）", "a" * 1000),
        ("长内容（10000字符）", "a" * 10000),
        ("超长内容（50000字符）", "a" * 50000),
    ]

    print("=" * 60)
    print("CodeValidator 性能测试")
    print("=" * 60)

    results = []

    for name, content in test_cases:
        # 预热
        validator.validate_content(content)

        # 正式测试：运行100次取平均值
        iterations = 100
        total_time = 0

        for _ in range(iterations):
            start = time.perf_counter()
            result = validator.validate_content(content)
            elapsed = time.perf_counter() - start
            total_time += elapsed

        avg_time_ms = (total_time / iterations) * 1000
        results.append((name, avg_time_ms, len(content)))

        # 打印结果
        print(f"\n{name}:")
        print(f"  - 内容长度: {len(content)} 字符")
        print(f"  - 平均验证时间: {avg_time_ms:.3f}ms (100次平均)")
        print(f"  - 性能评级: ", end="")

        # 性能评级
        if avg_time_ms < 1:
            print("✅ 优秀 (<1ms)")
        elif avg_time_ms < 5:
            print("✅ 良好 (<5ms)")
        elif avg_time_ms < 10:
            print("⚠️  可接受 (<10ms)")
        else:
            print("❌ 需要优化 (>=10ms)")

    # 性能总结
    print("\n" + "=" * 60)
    print("性能总结")
    print("=" * 60)

    # 验证所有测试都<10ms
    all_pass = all(avg < 10 for _, avg, _ in results)

    if all_pass:
        print("✅ 所有性能测试通过！")
        print("   验证器性能满足要求（<10ms）")
    else:
        print("❌ 部分性能测试未通过")
        print("   建议优化验证器性能")

    # 计算性能影响
    avg_validation_time = sum(avg for _, avg, _ in results) / len(results)
    continue_interval = 5000  # 5秒
    performance_impact = (avg_validation_time / continue_interval) * 100

    print(f"\n性能影响估算:")
    print(f"  - 平均验证时间: {avg_validation_time:.3f}ms")
    print(f"  - 续写间隔: {continue_interval}ms")
    print(f"  - 性能影响: {performance_impact:.3f}%")

    if performance_impact < 1:
        print(f"  - ✅ 性能影响可接受 (<1%)")
    else:
        print(f"  - ⚠️  性能影响需要注意 (>=1%)")

    return all_pass


if __name__ == "__main__":
    success = test_validator_performance()
    sys.exit(0 if success else 1)
