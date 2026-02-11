#!/usr/bin/env python3
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('password_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            from pwd_generator.cli import main_cli
            main_cli()
        else:
            from pwd_generator.interactive import main_interactive
            main_interactive()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error in main")
        print(f"\nFatal error: {e}")
        sys.exit(1)
