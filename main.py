"""
Entry point - RepCRec distributed concurrency control & recovery system.
"""

import sys
from parser import Parser

from transaction_manager import TransactionManager


class RepCRec:
    """
    RepCRec - orchestrates TransactionManager and dispatches commands.
    """

    def __init__(self):
        """
        Purpose: construct RepCRec facade.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: instantiates TransactionManager.
        """
        self.tm = TransactionManager()

    def execute_command(self, command: str, args: list):
        """
        Purpose: dispatch one parsed command to TM.
        Author: Xi Wang
        Args: command name; args list.
        Returns: None
        Side effects: executes TM operations and prints outputs.
        """
        if command == "begin":
            self.tm.begin(args[0])

        elif command == "beginRO":
            self.tm.begin_read_only(args[0])

        elif command == "read":
            self.tm.read(args[0], args[1])

        elif command == "write":
            self.tm.write(args[0], args[1], args[2])

        elif command == "end":
            self.tm.end(args[0])

        elif command == "fail":
            self.tm.fail(args[0])

        elif command == "recover":
            self.tm.recover(args[0])

        elif command == "dump":
            self.tm.dump()

        elif command == "dump_site":
            self.tm.dump_site(args[0])

        elif command == "dump_variable":
            self.tm.dump_variable(args[0])

        elif command == "querystate":
            self.tm.query_state()

        else:
            print(f"Unknown command: {command}")

    def run_from_file(self, filename: str):
        """
        Purpose: run commands from file.
        Author: Sihang Zhao
        Args: filename
        Returns: None
        Side effects: executes commands sequentially with time ticks.
        """
        commands = Parser.parse_file(filename)

        if not commands:
            print("No commands to execute")
            return

        print(f"=== Executing {len(commands)} commands from {filename} ===\n")

        for command, args in commands:
            # 时间推进
            self.tm.tick()

            # 执行命令
            self.execute_command(command, args)

        print("\n=== Execution completed ===")

        # 打印最终统计
        print(f"\nFinal statistics:")
        print(f"  Committed transactions: {len(self.tm.committed_transactions)}")
        print(f"  Aborted transactions: {len(self.tm.aborted_transactions)}")

    def run_from_stdin(self):
        """
        Purpose: run commands from stdin.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: executes commands with time ticks.
        """
        commands = Parser.parse_stdin()

        if not commands:
            print("No commands to execute")
            return

        print(f"\n=== Executing {len(commands)} commands ===\n")

        for command, args in commands:
            # 时间推进
            self.tm.tick()

            # 执行命令
            self.execute_command(command, args)

        print("\n=== Execution completed ===")

    def run_interactive(self):
        """
        Purpose: interactive REPL.
        Author: Sihang Zhao
        Args: None
        Returns: None
        Side effects: executes commands with time ticks.
        """
        print("=== RepCRec Interactive Mode ===")
        print("Enter commands one at a time (or 'quit' to exit):\n")

        while True:
            try:
                line = input("> ").strip()

                if line.lower() in ["quit", "exit", "q"]:
                    break

                if not line:
                    continue

                result = Parser.parse_line(line)
                if result:
                    command, args = result

                    # 时间推进
                    self.tm.tick()

                    # 执行命令
                    self.execute_command(command, args)

            except EOFError:
                break
            except KeyboardInterrupt:
                print("\nInterrupted")
                break

        print("\n=== Session ended ===")


def main():
    """
    Purpose: CLI entry.
    Author: Xi Wang
    Args: None
    Returns: None
    Side effects: launches file or interactive execution.
    """
    recrcrec = RepCRec()

    if len(sys.argv) > 1:
        # 从文件运行
        filename = sys.argv[1]
        recrcrec.run_from_file(filename)
    else:
        # 交互式模式
        print("RepCRec - Distributed Replicated Concurrency Control and Recovery")
        print("=" * 60)
        print("\nUsage:")
        print("  python main.py <input_file>  - Run commands from file")
        print("  python main.py               - Interactive mode")
        print("\n" + "=" * 60 + "\n")

        recrcrec.run_interactive()


if __name__ == "__main__":
    main()
