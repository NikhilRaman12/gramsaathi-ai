import gradio as gr
from scripts.generator import GramsaathiEngine  # adjust path if needed

# Initialize engine
engine = GramsaathiEngine()

def ask_query(user_input):
    # Pass query to engine
    response = engine.run(user_input)  # run() internally calls generate()
    return response

# Build Gradio interface
demo = gr.Interface(
    fn=ask_query,
    inputs=gr.Textbox(
        lines=2,
        placeholder="Ask about PM Kisan, PM Fasal Bima Yojana, rural development, sustainability..."
    ),
    outputs=gr.Textbox(label="Gramsaathi AI Response"),
    title="🌾 Gramsaathi AI – Rural Development & Sustainability Assistant",
    description=(
        "Gramsaathi AI is a RAG-based assistant designed to support farmers and rural communities. "
        "It uses real government scheme data, AWS Bedrock integration, and guardrails for safe, "
        "grounded answers. Ask about agriculture, rural development, or sustainability initiatives."
    )
)

if __name__ == "__main__":
    demo.launch(share=True)
