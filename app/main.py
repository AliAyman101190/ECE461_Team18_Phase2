import warnings
import sys

# Suppress noisy RequestsDependencyWarning emitted by system-installed requests
# when urllib3/chardet versions are different than expected. Do this before
# importing any module that may import `requests`.
warnings.filterwarnings("ignore", module=r"requests.*")

from cli_controller import CLIController

def main() -> None:
    controller = CLIController()
    exit_code = controller.run()
    # print(exit_code) # for debugging
    sys.exit(exit_code)

if __name__ == '__main__':
    main()