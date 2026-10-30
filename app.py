"""Gramsaathi One Gradio application."""

from __future__ import annotations

import html
import os
from collections.abc import Sequence
from typing import Any

import gradio as gr

from scripts.eligibility import ALL_FIELDS, check_pm_kisan
from scripts.generator import GramsaathiEngine


engine: GramsaathiEngine | None = None


def _get_engine() -> GramsaathiEngine:
    global engine
    if engine is None:
        engine = GramsaathiEngine()
    return engine

CSS = """
:root { --gs-green: #176b4b; --gs-ink: #18302a; --gs-soft: #f3f7f3; }
body, .gradio-container { background: #f4f7f4 !important; color: var(--gs-ink); }
#hero { padding: 1.5rem 1.5rem 1.2rem; border-radius: 22px; background: linear-gradient(120deg,#e8f4ec,#fbf8eb); border: 1px solid #d8e6da; }
#hero h1 { margin: 0 0 .5rem; color: #143e30; font-size: clamp(1.9rem,4vw,2.7rem); }
#hero p { margin: .35rem 0; max-width: 72ch; color: #3d5148; }
.panel { border: 1px solid #dbe5de !important; border-radius: 18px !important; background: #fff !important; }
.primary-button { background: #176b4b !important; color: white !important; border: 0 !important; }
.result-card { border: 1px solid #dce7df; border-radius: 14px; background: white; padding: 1rem 1.2rem; margin: .65rem 0; }
.result-card h3 { margin: 0 0 .6rem; color: #174c39; font-size: 1.1rem; }
.status-pill { display: inline-block; padding: .3rem .7rem; border-radius: 99px; font-weight: 650; background: #e9f2ec; color: #18543c; }
.status-warning { background: #fff2d7; color: #704b00; }
.source-card { margin: .6rem 0; border-left: 4px solid #74a78a; padding: .8rem 1rem; background: #f7faf7; border-radius: 6px; }
.source-card p { margin: .35rem 0; line-height: 1.5; }
a { color: #075fbd; text-decoration-thickness: 1px; text-underline-offset: 2px; }
button:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid #b27613 !important; outline-offset: 2px !important; }
@media (max-width: 640px) { #hero { padding: 1.1rem; border-radius: 14px; } .result-card { padding: .85rem; } }
"""


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _card(title: str, body: str) -> str:
    if not body:
        return ""
    return f'<section class="result-card"><h3>{_escape(title)}</h3>{body}</section>'


def _list_html(items: Sequence[str], *, ordered: bool = False) -> str:
    if not items:
        return ""
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{_escape(item)}</li>" for item in items) + f"</{tag}>"


def render_response(result: dict[str, Any]) -> str:
    """Render model and source content as escaped HTML."""
    status = result.get("status", "provider_error")
    messages = {
        "empty_query": "Start with one clear question. Add your location and crop or scheme when relevant.",
        "no_evidence": result.get("message", "No matching evidence was found."),
        "provider_error": result.get("message", "The answer service is not available."),
        "invalid_output": result.get("message", "The response could not be validated."),
        "ok": "Evidence-based guidance",
    }
    warning = status in {"no_evidence", "provider_error", "invalid_output"}
    badge_class = "status-pill status-warning" if warning else "status-pill"
    output = [f'<div class="{badge_class}">{_escape(messages.get(status, status))}</div>']

    summary_items = []
    for item in result.get("summary", []):
        refs = ", ".join(item.get("source_ids", []))
        summary_items.append(f"{item.get('text', '')}" + (f" [{refs}]" if refs else ""))
    output.append(_card("What the sources say", _list_html(summary_items)))

    action_items = []
    for item in result.get("action_plan", []):
        refs = ", ".join(item.get("source_ids", []))
        action_items.append(f"{item.get('step', '')}" + (f" [{refs}]" if refs else ""))
    output.append(_card("Practical next steps", _list_html(action_items, ordered=True)))

    missing = result.get("missing_information", [])
    questions = result.get("follow_up_questions", [])
    missing_body = _list_html(missing + questions)
    output.append(_card("What would make this more specific", missing_body))
    output.append(_card("Uncertainty and conflicts", _list_html(result.get("uncertainties", []))))

    evidence_cards = []
    for item in result.get("evidence", []):
        source_id = _escape(item.get("id", ""))
        title = _escape(item.get("source_title", item.get("source_file", "Source")))
        file_name = _escape(item.get("source_file", ""))
        page = item.get("page")
        page_text = f"Page {_escape(page)}" if page is not None else "Text source"
        date_text = f" · Document date: {_escape(item['source_date'])}" if item.get("source_date") else ""
        urls = []
        for url in item.get("source_urls", []):
            if isinstance(url, str) and url.startswith(("https://", "http://")):
                safe_url = _escape(url)
                urls.append(f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">Open source</a>')
        links = " · ".join(urls) if urls else "No link embedded on this page"
        snippet = _escape(item.get("text", ""))
        evidence_cards.append(
            '<article class="source-card">'
            f"<strong>[{source_id}] {title}</strong><br>"
            f"<small>{file_name} · {page_text}{date_text}</small>"
            f"<p>{snippet}</p><small>{links}</small>"
            "</article>"
        )
    output.append(_card("Evidence", "".join(evidence_cards)))
    return "".join(part for part in output if part)


def respond(query: str, language: str) -> str:
    return render_response(_get_engine().run(query, language))


_FIELD_LABELS = {
    "landholding_farmer": "Cultivable land is recorded in the State/UT land records for a family member? / किसान परिवार के सदस्य के नाम राज्य/केंद्रशासित प्रदेश के भूमि रिकॉर्ड में खेती योग्य भूमि है?",
    "institutional_landholder": "Is the landholder an institution? / क्या भूमि धारक कोई संस्था है?",
    "constitutional_post_holder": "Has any family member held a constitutional post? / क्या परिवार के किसी सदस्य ने संवैधानिक पद संभाला है?",
    "political_or_local_office_holder": "Has any family member been a minister, MP, MLA/MLC, municipal corporation mayor, or district panchayat chairperson? / क्या परिवार का कोई सदस्य मंत्री, सांसद, विधायक/विधान परिषद सदस्य, नगर निगम महापौर या जिला पंचायत अध्यक्ष रहा है?",
    "non_exempt_government_employee": "Is any family member a serving/retired government, PSU, autonomous-institution, or regular local-body employee other than MTS/Class IV/Group D? / क्या परिवार का कोई सदस्य MTS/Class IV/Group D को छोड़कर केंद्र/राज्य सरकार, PSU, स्वायत्त संस्था या स्थानीय निकाय का कर्मचारी/सेवानिवृत्त कर्मचारी है?",
    "pension_10000_or_more": "Does any family member receive a monthly government pension of ₹10,000 or more, other than an MTS/Class IV/Group D pensioner? / क्या MTS/Class IV/Group D को छोड़कर परिवार के किसी सदस्य की सरकारी पेंशन ₹10,000 प्रति माह या अधिक है?",
    "income_tax_payer": "Did any family member pay income tax in the last assessment year? / क्या पिछले आकलन वर्ष में परिवार के किसी सदस्य ने आयकर दिया?",
    "practicing_registered_professional": "Is any family member a registered doctor, engineer, lawyer, chartered accountant, or architect currently practising? / क्या परिवार का कोई सदस्य पंजीकृत डॉक्टर, इंजीनियर, वकील, चार्टर्ड अकाउंटेंट या वास्तुकार के रूप में काम कर रहा है?",
    "ownership_after_2019_02_01": "Was the cultivable land acquired after 1 February 2019? / क्या खेती योग्य भूमि 1 फरवरी 2019 के बाद प्राप्त हुई?",
    "multiple_family_recipients": "Are multiple members of the family receiving PM-KISAN benefits? / क्या परिवार के एक से अधिक सदस्य PM-KISAN लाभ ले रहे हैं?",
}


def _screen_answer(value: str | None) -> bool | None:
    if not value:
        return None
    answer = value.split("/", 1)[0].strip().casefold()
    if answer == "yes":
        return True
    if answer == "no":
        return False
    return None


def render_pm_kisan_screen(*values: str) -> str:
    facts = {field: _screen_answer(value) for field, value in zip(ALL_FIELDS, values)}
    result = check_pm_kisan(facts)
    status_label = {
        "possible_exclusion": "Possible listed exclusion",
        "landholding_requirement_not_confirmed": "Landholding requirement not confirmed",
        "needs_more_information": "More information needed",
        "no_listed_exclusion_found": "No listed exclusion found in these answers",
    }.get(result["status"], "Preliminary screen")
    parts = [
        '<section class="result-card">',
        f"<h3>{_escape(status_label)}</h3>",
        f"<p>{_escape(result['message'])}</p>",
        f"<p><strong>Family definition:</strong> {_escape(result['family_definition'])}</p>",
    ]
    if result["missing_information"]:
        questions = [item["question"] for item in result["missing_information"]]
        parts.append(f"<p><strong>Still unknown:</strong></p>{_list_html(questions)}")
    if result["matched_exclusions"]:
        labels = [_FIELD_LABELS.get(name, name) for name in result["matched_exclusions"]]
        parts.append(f"<p><strong>Answers to confirm:</strong></p>{_list_html(labels)}")
    if result["cautions"]:
        parts.append(f"<p><strong>Official portal cautions:</strong></p>{_list_html(result['cautions'])}")
    parts.extend(
        [
            f'<p><a href="{_escape(result["source_url"])}" target="_blank" rel="noopener noreferrer">'
            f"{_escape(result['source_title'])}</a> · Rules checked { _escape(result['rules_checked_at']) }</p>",
            f"<small>{_escape(result['disclaimer'])}</small>",
            "</section>",
        ]
    )
    return "".join(parts)


def _build_app() -> gr.Blocks:
    theme = gr.themes.Soft(primary_hue="green", secondary_hue="amber", neutral_hue="slate")
    with gr.Blocks(theme=theme, css=CSS, title="Gramsaathi One") as demo:
        gr.Markdown(
            "# 🌾 Gramsaathi One\n"
            "### Rural Intelligence & Action Agent\n"
            "Describe a farming or rural-development question. Gramsaathi searches the included documents, "
            "shows the evidence it found, and separates next steps from missing information and uncertainty.",
            elem_id="hero",
        )
        with gr.Row(equal_height=False):
            with gr.Column(scale=5):
                with gr.Group(elem_classes=["panel"]):
                    query = gr.Textbox(
                        label="What do you need help with?",
                        placeholder="Example: My PM-KISAN payment is delayed in [district, state]. What should I check?",
                        lines=4,
                        max_lines=8,
                    )
                    language = gr.Radio(
                        choices=[("English", "en"), ("हिंदी", "hi")],
                        value="en",
                        label="Answer language",
                    )
                    ask_button = gr.Button("Find evidence and next steps", variant="primary", elem_classes=["primary-button"])
                gr.HTML(
                    "<small>Use the guidance as a starting point. Official sources and their page numbers are shown "
                    "when available; local authorities make final scheme decisions.</small>"
                )
            with gr.Column(scale=7):
                result_output = gr.HTML(
                    render_response({"status": "empty_query", "summary": [], "action_plan": [], "evidence": []}),
                    label="Response",
                )

        ask_button.click(respond, inputs=[query, language], outputs=result_output, show_progress="full")
        query.submit(respond, inputs=[query, language], outputs=result_output, show_progress="full")

        with gr.Accordion("Optional: PM-KISAN preliminary screen", open=False):
            gr.Markdown(
                "Answer for the farmer's family (husband, wife and minor children, as described by the scheme). "
                "Choose **Not sure** when a fact is unknown. These answers are processed in this session and are not saved by the checker."
            )
            screen_inputs = []
            screen_choices = ["Not sure / पता नहीं", "Yes / हाँ", "No / नहीं"]
            for field in ALL_FIELDS:
                screen_inputs.append(
                    gr.Radio(
                        choices=screen_choices,
                        value=screen_choices[0],
                        label=_FIELD_LABELS[field],
                    )
                )
            screen_button = gr.Button("Check against published PM-KISAN rules")
            screen_output = gr.HTML(
                "<small>This is a preliminary screen, not an official eligibility or payment decision.</small>"
            )
            screen_button.click(render_pm_kisan_screen, inputs=screen_inputs, outputs=screen_output, show_progress="hidden")

        gr.Markdown(
            "---\n"
            "**How to read this:** `[S1]` labels connect statements and steps to the evidence cards. "
            "The included library mixes official documents, research, and older material; check the cited source's date and link before acting."
        )
    return demo


demo = _build_app()

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
