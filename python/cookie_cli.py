import argparse
from utils.config import Configuration


if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Manage seeds and cookies")

    # Add arguments
    parser.add_argument("-a", action="store_true", help="Add a cookie to the file")
    parser.add_argument("-r", action="store_true", help="Remove a seed or cookie")
    parser.add_argument("seed", help="Seed value")
    parser.add_argument("cookie", nargs="?", help="Cookie value (optional). Insert the cookie inside \"...\"")

    # Parse the command-line arguments
    args = parser.parse_args()

    config = Configuration()

    # Process the arguments
    if args.a:
        if args.cookie is None:
            print("Please provide a cookie value with -a option.")
        else:
            config.add_cookie(args.seed, args.cookie)
            print("Cookie updated successfully!")

    elif args.r:
        if args.cookie is None:
            config.remove_seed(args.seed)
            print(f"Seed {args.seed} removed.")
        else:
            config.remove_cookie(args.seed, args.cookie)
            print("Cookie removed.")

    else:
        print("Please provide a valid option (-a or -r).")