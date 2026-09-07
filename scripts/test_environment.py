import os
from dotenv import load_dotenv

load_dotenv()

def main():
  print("Threat Intelligence RAG System")
  print("Environment setup successful.")
  print(f"Environment mode: {os.getenv('ENVIRONMENT', 'not set')}")

if __name__ == "__main__":
  main()