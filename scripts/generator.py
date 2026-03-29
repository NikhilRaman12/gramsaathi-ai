"""
Gramsaathi AI - Simple RAG Demo Version

- FAISS retrieval
- AWS Bedrock (Nemotron)
- No strict filters (demo-friendly)
"""

from scripts.retriever import Retriever
import boto3, json


class AgroLLMEngine:
    def __init__(self, model_id="nvidia.nemotron-nano-12b-v2", region="us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def generate(self, prompt):
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
            "temperature": 0.5
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body
        )

        result = json.loads(response["body"].read())

        try:
            return result["choices"][0]["message"]["content"].strip()
        except Exception:
            return "Sorry, could not generate response."


class GramsaathiEngine:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = AgroLLMEngine()

    def build_prompt(self, context, query):
        return f"""You are Gramsaathi AI, an agriculture assistant.

Use the below context to answer the question.
If context is not enough, give a general helpful answer.

Context:
{context}

Question:
{query}
"""

    def run(self, query):
        if not query.strip():
            return "Please enter a valid question."

        # Get context
        context = self.retriever.get_context(query)

        # Build prompt
        prompt = self.build_prompt(context, query)

        # Generate answer
        answer = self.llm.generate(prompt)

        return answer


if __name__ == "__main__":
    app = GramsaathiEngine()
    print("Gramsaathi AI running...\n")

    while True:
        query = input("Ask: ")
        if query.lower() == "exit":
            break

        response = app.run(query)
        print("\nAnswer:\n", response)
        print("\n" + "-"*50 + "\n")
