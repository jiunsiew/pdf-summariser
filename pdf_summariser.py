import os
import sys
import argparse
from typing import List
from openai import OpenAI
from dotenv import load_dotenv


def summarise_url(client: OpenAI, url: str, model: str = "gpt-3.5-turbo") -> dict:
    """Ask the LLM to read and summarize the PDF at the given URL.

    This assumes the model has the capability to fetch and read the URL directly.
    """
    try:
        # use this: https://platform.openai.com/docs/api-reference/responses/create?lang=python
        prompt = (
            "You are a concise document summariser. Read the PDF at the provided URL directly and "
            "return a clear, structured summary with key points, important details, and conclusions."
            # f"Here is a PDF URL. Please fetch it directly, read it, and provide a concise summary in bullet points, "
            # f"then a short paragraph recap.\n\nURL: {url}"
        )
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text",
                         "text": prompt
                        },
                        {"type": "input_file",
                         "file_url": url}
                    ],
                }
            ],
            temperature=0.3,
            max_output_tokens=800,
        )
        id = resp.id
        model_used = resp.model
        text = resp.output[0].content[0].text

        output = {"response_id": id, "model": model_used, "summary": text.strip()}
        return output
    except Exception as e:
        return {"response_id": None, "model": None,"summary": f"Error summarizing {url}: {str(e)}"}


def process_urls(urls: List[str], output_file: str, api_key: str, model: str) -> None:
    client = OpenAI(api_key=api_key)

    outputs = []
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Summarizing: {url}")
        summary = summarize_url(client, url, model=model)
        outputs.append(
            f"URL: {url}\n"
            f"Summary:\n{summary}\n"
            f"{'='*80}\n\n"
        )

    # Ensure parent directory exists
    out_dir = os.path.dirname(os.path.abspath(output_file))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(outputs)

    print(f"\nSaved summaries to: {os.path.abspath(output_file)}")


def main():
    # parser = argparse.ArgumentParser(
    #     description="Summarize PDFs by passing their URLs directly to the LLM (no local downloading/parsing)",
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    # )
    # parser.add_argument("urls", nargs="+", help="One or more PDF URLs")
    # parser.add_argument("--output", "-o", default="summaries.txt", help="Output text file for summaries")
    # parser.add_argument(
    #     "--api-key",
    #     default=os.getenv("OPENAI_API_KEY"),
    #     help="OpenAI API key (or set OPENAI_API_KEY env var)",
    # )
    # parser.add_argument(
    #     "--model",
    #     default="gpt-3.5-turbo",
    #     help="Model to use (must support direct URL fetching in your account)",
    # )

    # args = parser.parse_args()

    # # Load environment variables from .env file and re-check api key
    # load_dotenv()
    # if not args.api_key:
    #     args.api_key = os.getenv("OPENAI_API_KEY")

    # if not args.api_key:
    #     print("Error: OPENAI_API_KEY not set. Provide via --api-key or environment variable.")
    #     sys.exit(1)

    # process_urls(args.urls, args.output, api_key=args.api_key, model=args.model)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    model='gpt-4.1-nano'
    url="https://www.berkshirehathaway.com/letters/2024ltr.pdf"
    client = OpenAI(api_key=api_key)



if __name__ == "__main__":
    main()
