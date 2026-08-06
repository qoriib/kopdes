import sys
import subprocess
import yaml

def get_ref(name):
    try:
        out = subprocess.check_output(["git", "show-ref"]).decode("utf-8")
        for line in out.splitlines():
            # Matches format like: "commit_sha refs/exps/baseline_sha/name"
            if f"/{name}" in line:
                return line.split()[1]
    except Exception as e:
        print(f"Error fetching ref for {name}: {e}")
    return None

def checkout(name):
    ref = get_ref(name)
    if not ref:
        print(f"Error: Ref for {name} not found.")
        sys.exit(1)
    print(f"Checking out dvc.lock from {ref}")
    subprocess.check_call(["git", "checkout", ref, "--", "dvc.lock"])

def merge(names):
    merged = {"schema": "2.0", "stages": {}}
    for name in names:
        ref = get_ref(name)
        if not ref:
            print(f"Error: Ref for {name} not found.")
            sys.exit(1)
        print(f"Merging dvc.lock from {ref}")
        content = subprocess.check_output(["git", "show", f"{ref}:dvc.lock"]).decode("utf-8")
        lock_data = yaml.safe_load(content) or {}
        merged["stages"].update(lock_data.get("stages", {}))
    
    with open("dvc.lock", "w") as f:
        yaml.dump(merged, f)
    print("Merged dvc.lock successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python dvc_exp_helper.py <command> <args...>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "checkout":
        checkout(sys.argv[2])
    elif cmd == "merge":
        merge(sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
