from bs4 import BeautifulSoup
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
import json
import pandas as pd
import requests
from typing import Dict, List
from tqdm.auto import tqdm

from prompts.templates.job_analysis import prompt_template
from prompts.references.health_science_courses import health_science_courses

def links_to_df(
        sources: List[str]
):
    rows = []
    for url in sources:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        json_ld = soup.find("script", type="application/ld+json")
        job = json.loads(json_ld.string)

        rows.append({
            "title": job["title"],
            "posted": job["datePosted"],
            "deadline": job["validThrough"],
            "location": job["jobLocation"]["address"]["addressLocality"],
            "employer": job["hiringOrganization"]["name"],
            "job_id": job["identifier"]["value"],
            "type": job["employmentType"],
            "description": job["description"],
            "url": url,
        })

    return pd.DataFrame(rows)

def build_pipeline(
    model: str = "ministral-3:8b",
    prompt_template: str = prompt_template,
    ollama_url: str = "http://localhost:11434",
    ollama_temperature: float = 0.0,
) -> Pipeline:
    prompt_builder = PromptBuilder(
        template=prompt_template,
        required_variables=["health_science_courses", "job"],
    )

    generator = OllamaChatGenerator(
        model=model,
        url=ollama_url,
        generation_kwargs={
            "temperature": ollama_temperature,
        },
        response_format="json",
    )

    pipeline = Pipeline()

    pipeline.add_component("prompt_builder", prompt_builder)
    pipeline.add_component("generator", generator)
    pipeline.connect("prompt_builder", "generator")

    return pipeline

def process_jobs(
    sources: List,
    pipeline: Pipeline,
) -> List[Dict]:
    df = links_to_df(sources)

    processed_jobs = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        row_dict = row.to_dict()

        job = f"""
Job title: {row.get("title", "")}

Job posting date: {row.get("posted", "")}

Job application deadline: {row.get("deadline", "")}

Job location: {row.get("location", "")}

Job employer: {row.get("employer", "")}

Job ID: {row.get("job_id", "")}

Job type: {row.get("type", "")}

Job description: {row.get("description", "")}
"""

        response_dict = json.loads(pipeline.run({
            "prompt_builder": {
                "health_science_courses": health_science_courses,
                "job": job,
            }
        })["generator"]["replies"][0].text)

        response_dict_checked = {
            "health_science_related": response_dict.get("health_science_related", ""),
            "masters_required": response_dict.get("masters_required", ""),
            "doctorate_required": response_dict.get("doctorate_required", ""),
            "language_of_work": response_dict.get("language_of_work", "")
        }

        processed_jobs.append(row_dict | response_dict_checked)
    
    return processed_jobs

if __name__ == "__main__":
    pipeline = build_pipeline()

    sources = [
        "https://uottawa.wd3.myworkdayjobs.com/en-US/uOttawa_External_Career_Site/job/Lees-Campus/CUPE-SUMMER-2026-TA-HSS1101X-ISHS--40h-_JR33289?jobFamilyGroup=f04d695cd5b5100e92c05a3151910000",
        "https://uottawa.wd3.myworkdayjobs.com/en-US/uOttawa_External_Career_Site/job/Lees-Campus/CUPE---SUMMER-2026-TA---HSS2105X---ISHS--80h-_JR33315?jobFamilyGroup=f04d695cd5b5100e92c05a3151910000",
        "https://uottawa.wd3.myworkdayjobs.com/en-US/uOttawa_External_Career_Site/job/Lees-Campus/CUPE-Summer-2026-TA-HSS2305X--ISHS--70h-_JR33314?jobFamilyGroup=f04d695cd5b5100e92c05a3151910000",
    ]

    df_processed = pd.DataFrame(process_jobs(sources, pipeline))

    print(json.dumps(df_processed.to_dict(orient="records"), indent=2))