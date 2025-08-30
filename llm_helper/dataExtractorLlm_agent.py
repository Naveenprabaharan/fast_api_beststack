import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict,Literal
from IPython.display import display, Image
import operator
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv()


os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0)

def get_data_for_domain(res):
    enriched_result = []

    for row in res:
        software_data = {
            "domain": row[0],
            "software_name": row[1],
            "software_url": row[2],
            "features": row[3],
            "feature_descriptions": row[4]
        }

        # Prepare prompt or question for LLM
        prompt = f"""Based on the following features and descriptions for {software_data['software_name']} ({software_data['software_url']}), provide an overview including price-related info and other relevant insights:
Features: {', '.join(software_data['features'])}
Descriptions: {', '.join(software_data['feature_descriptions'])}
"""

        # Query LLM for enriched info
        llm_response = llm.invoke(prompt)

        software_data["llm_summary"] = llm_response

        enriched_result.append(software_data)
        print(f'enriched_result : {enriched_result}')

    return {"status": "success", "data": enriched_result}
