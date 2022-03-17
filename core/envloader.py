import os

CURRENT_DOTENV = os.path.join(os.path.dirname(__file__), ".env")


def load_env():
    if not os.path.exists(CURRENT_DOTENV):
        print("Env file not found")
        return

    print(f"READING DOTENV FROM: {CURRENT_DOTENV}", end="\n")
    with open(CURRENT_DOTENV, "r") as file:
        for line in file.readlines():
            var, value = line.replace("\n", "").split("=")
            os.environ[var] = value
