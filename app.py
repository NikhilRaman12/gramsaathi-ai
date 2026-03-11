import gradio as gr
import boto3
import json
import os

# Configure AWS Bedrock client
# Make sure your AWS credentials are set in the environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

MODEL_ID = "anthropic.claude-v2"  # Example model, replace with the one you want

def gramsaathi(query: str) -> str:
    """
    Send farmer query to Bedrock model and return AI advice.
    """
    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "prompt": f"Farmer question: {query}\nProvide clear, practical agricultural advice.",
                "max_tokens_to_sample": 300
            })
        )
        result = json.loads(response["body"].read())
        return "🌾 GramSaathi AI advice: " + result.get("completion", "").strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Gradio interface
demo = gr.Interface(
    fn=gramsaathi,
    inputs=gr.Textbox(lines=2, placeholder="Ask about crops, soil, irrigation..."),
    outputs="text",
    title="GramSaathi AI (Bedrock)",
    description="AI assistant for farmers powered by AWS Bedrock"
)

if __name__ == "__main__":
    demo.launch()
