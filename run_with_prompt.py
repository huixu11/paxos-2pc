import os
import subprocess
import sys


def main():
    """Run paxos_p3.da with PROMPT_BALANCE enabled and pass through stdio."""
    env = os.environ.copy()
    env.setdefault("PROMPT_BALANCE", "1")
    # Allow overriding test file by passing it as the first argument
    args = [sys.executable, "-u", "-m", "da", "paxos_p3.da"]
    if len(sys.argv) > 1:
        # Pass test CSV as positional arg to paxos_p3.da
        args.append(sys.argv[1])
    print(f"Running with PROMPT_BALANCE={env['PROMPT_BALANCE']} ->", " ".join(args))
    try:
        subprocess.run(args, env=env, check=False)
    except KeyboardInterrupt:
        print("Interrupted")


if __name__ == "__main__":
    main()
