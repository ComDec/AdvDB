"""
输入解析器 - 解析项目指令
"""

import re
from typing import List, Optional, Tuple


class Parser:
    """
    Parser - 解析项目输入指令

    支持的指令格式：
    - begin(T1)
    - beginRO(T1)
    - R(T1, x1)
    - W(T1, x1, 100)
    - end(T1)
    - fail(1)
    - recover(1)
    - dump()
    - dump(1)
    - dump(x1)
    """

    @staticmethod
    def parse_line(line: str) -> Optional[Tuple[str, List]]:
        """
        解析一行输入

        Args:
            line: 输入行

        Returns:
            (command, args) 元组，如果解析失败则返回None
        """
        # 移除空白和注释
        line = line.strip()

        # 跳过空行
        if not line:
            return None

        # 跳过注释（以//开头）
        if line.startswith("//"):
            return None

        # 移除行内注释
        comment_pos = line.find("//")
        if comment_pos != -1:
            line = line[:comment_pos].strip()

        # begin(T1)
        match = re.match(r"begin\((\w+)\)", line)
        if match:
            return ("begin", [match.group(1)])

        # beginRO(T1)
        match = re.match(r"beginRO\((\w+)\)", line)
        if match:
            return ("beginRO", [match.group(1)])

        # R(T1, x1)
        match = re.match(r"R\((\w+),\s*(\w+)\)", line)
        if match:
            return ("read", [match.group(1), match.group(2)])

        # W(T1, x1, 100)
        match = re.match(r"W\((\w+),\s*(\w+),\s*(-?\d+)\)", line)
        if match:
            return ("write", [match.group(1), match.group(2), int(match.group(3))])

        # end(T1)
        match = re.match(r"end\((\w+)\)", line)
        if match:
            return ("end", [match.group(1)])

        # fail(1)
        match = re.match(r"fail\((\d+)\)", line)
        if match:
            return ("fail", [int(match.group(1))])

        # recover(1)
        match = re.match(r"recover\((\d+)\)", line)
        if match:
            return ("recover", [int(match.group(1))])

        # dump()
        if line == "dump()":
            return ("dump", [])

        # dump(1)
        match = re.match(r"dump\((\d+)\)", line)
        if match:
            return ("dump_site", [int(match.group(1))])

        # dump(x1)
        match = re.match(r"dump\((\w+)\)", line)
        if match:
            return ("dump_variable", [match.group(1)])

        # 未知指令
        print(f"Warning: Unknown command: {line}")
        return None

    @staticmethod
    def parse_file(filename: str) -> List[Tuple[str, List]]:
        """
        解析输入文件

        Args:
            filename: 输入文件路径

        Returns:
            指令列表
        """
        commands = []

        try:
            with open(filename) as f:
                for line in f:
                    result = Parser.parse_line(line)
                    if result:
                        commands.append(result)
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

        return commands

    @staticmethod
    def parse_stdin() -> List[Tuple[str, List]]:
        """
        从标准输入解析指令

        Returns:
            指令列表
        """
        commands = []

        print("Enter commands (Ctrl+D to finish):")
        try:
            while True:
                line = input()
                result = Parser.parse_line(line)
                if result:
                    commands.append(result)
        except EOFError:
            pass

        return commands
