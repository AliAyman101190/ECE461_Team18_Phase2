import sys
from cli_controller import CLIController

def main() -> None:
    controller = CLIController()
    exit_code = controller.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()