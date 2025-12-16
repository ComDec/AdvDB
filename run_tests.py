#!/usr/bin/env python3
"""
批量运行 tests 文件夹中的所有测试用例
"""

import os
import sys
import subprocess
from pathlib import Path

def run_test(test_file):
    """运行单个测试文件并返回结果"""
    try:
        result = subprocess.run(
            [sys.executable, "main.py", test_file],
            capture_output=True,
            text=True,
            timeout=30  # 30秒超时
        )
        return {
            "file": test_file,
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "file": test_file,
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "测试超时（超过30秒）"
        }
    except Exception as e:
        return {
            "file": test_file,
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"运行错误: {str(e)}"
        }

def main():
    """主函数：运行所有测试"""
    tests_dir = Path("tests")
    
    if not tests_dir.exists():
        print(f"错误: tests 文件夹不存在")
        sys.exit(1)
    
    # 获取所有 .txt 测试文件
    test_files = sorted(tests_dir.glob("*.txt"))
    
    if not test_files:
        print(f"错误: tests 文件夹中没有找到 .txt 文件")
        sys.exit(1)
    
    # 创建日志文件
    log_file = Path("test_results.log")
    log_content = []
    
    header = "=" * 80 + "\n"
    header += f"测试运行日志 - {len(test_files)} 个测试用例\n"
    header += "=" * 80 + "\n\n"
    log_content.append(header)
    print(header, end="")
    
    results = []
    passed = 0
    failed = 0
    
    for i, test_file in enumerate(test_files, 1):
        test_header = f"\n{'=' * 80}\n"
        test_header += f"[{i}/{len(test_files)}] 测试文件: {test_file.name}\n"
        test_header += f"{'=' * 80}\n"
        
        log_content.append(test_header)
        print(test_header, end="")
        
        result = run_test(str(test_file))
        results.append(result)
        
        # 记录测试输出
        test_output = f"\n--- 测试输出 ---\n"
        if result["stdout"]:
            test_output += result["stdout"]
        if result["stderr"]:
            test_output += "\n--- 错误输出 ---\n"
            test_output += result["stderr"]
        
        test_output += f"\n--- 执行结果 ---\n"
        if result["success"]:
            passed += 1
            test_output += f"✓ 通过 (返回码: {result['returncode']})\n"
            print(f"  ✓ 通过")
        else:
            failed += 1
            test_output += f"✗ 失败 (返回码: {result['returncode']})\n"
            print(f"  ✗ 失败 (返回码: {result['returncode']})")
            if result["stderr"]:
                print(f"    错误: {result['stderr'][:200]}")
        
        log_content.append(test_output + "\n")
        print(test_output)
    
    # 生成摘要
    summary = "\n" + "=" * 80 + "\n"
    summary += "测试摘要\n"
    summary += "=" * 80 + "\n"
    summary += f"总测试数: {len(test_files)}\n"
    summary += f"通过: {passed} ({passed/len(test_files)*100:.1f}%)\n"
    summary += f"失败: {failed} ({failed/len(test_files)*100:.1f}%)\n"
    summary += "\n"
    
    # 失败的测试详情
    if failed > 0:
        summary += "失败的测试详情:\n"
        summary += "-" * 80 + "\n"
        for result in results:
            if not result["success"]:
                summary += f"\n文件: {result['file']}\n"
                summary += f"返回码: {result['returncode']}\n"
                if result["stderr"]:
                    summary += f"错误信息:\n{result['stderr']}\n"
                if result["stdout"]:
                    summary += f"输出:\n{result['stdout']}\n"
                summary += "-" * 80 + "\n"
    
    log_content.append(summary)
    print(summary)
    
    # 写入日志文件
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("".join(log_content))
    
    print(f"\n完整日志已保存到: {log_file}")
    
    # 返回适当的退出码
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()

