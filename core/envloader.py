import os

dot_env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def load_env():
    if not os.path.exists(dot_env_file):
        print("Env file not found")
        return

    print(f"Setting environment variables from: {dot_env_file}", end="\n")
    with open(dot_env_file, "r") as file:
        for line in file.readlines():
            var, value = line.replace("\n", "").split("=")
            os.environ[var] = value