import sys
import json

def main():
    try:
        context = json.load(sys.stdin)
        command = context.get("tool_args", {}).get("CommandLine", "")

        blocked_keywords = ["rm -rf", "mkfs", "dd if=", "format c:"]
        for kw in blocked_keywords:
            if kw in command.lower():
                print(f"BLOCKED: Destructive command keyword '{kw}' detected.", file=sys.stderr)
                sys.exit(1)

        print("APPROVED: Command validation passed.")
        sys.exit(0)
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
