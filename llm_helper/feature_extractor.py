#### Routing

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



# Graph state
class State(TypedDict):
    feature_content:str = Field(description="Feature relevant to SaaS for startups")
    domain:str
    feedback:str
    valid_json : str

# Scema for structured output to use in evaluation
class Feedback(BaseModel):
    grade: Literal['valid', 'not valid'] = Field(
        description="decide the feature_content is json valid or not."
    )
    feedback:str = Field(
        description="If the feature_content is not valid, provide feedback on how to improve it."
    )
    
# Augment the LLM with scema for structured output
evaluator = llm.with_structured_output(Feedback)

# Nodes
def llm_call_generator(state: State):
    """You are an expert SaaS product advisor."""
    
    if state.get("feedback"):
        msg = llm.invoke(
            f"List key features and descriptions to consider when selecting {state['domain']} SaaS for a startup. Return output as JSON with feature and feature_description fields. \
            but take into account the feedback: {state['feedback']}"
            )
    else:
        msg = llm.invoke(f"List key features and descriptions to consider when selecting {state['domain']} SaaS for a startup. Return output as JSON with feature and feature_description fields.")

    return {"feature_content": msg.content}


def llm_call_evaluator(state:State):
    """LLm evaluates the feature content for an startup"""
    
    grade = evaluator.invoke(f"Grade the content {state['feature_content']}")
    return {"valid_json":grade.grade, "feedback": grade.feedback}


# Conditional edges fucntion to route back to joke generator or end based upon feedback from the evaluator

def route_feature(state:State):
    """Routes back to feature generator or end based upon the feedback from the evaluator"""
    
    if state['valid_json']=='valid':
        return 'Accepted'
    elif state['valid_json']=="not valid":
        return "Rejected + Feedback"
    
# Building workflow
optimizer_builder = StateGraph(State)

# Add the nodes
optimizer_builder.add_node('llm_call_generator',llm_call_generator)
optimizer_builder.add_node('llm_call_evaluator',llm_call_evaluator)

# Add the edges
optimizer_builder.add_edge(START, 'llm_call_generator')
optimizer_builder.add_edge( 'llm_call_generator', 'llm_call_evaluator')
optimizer_builder.add_conditional_edges(
    'llm_call_evaluator',
    route_feature,
    {
    'Accepted' :END,
    'Rejected + Feedback':"llm_call_generator"
 }   ,
)


# Compile the workflow
optimizer_workflow = optimizer_builder.compile()

# Show the workflow
# display(Image(optimizer_workflow.get_graph().draw_mermaid_png()))

# Invoke 
def feature_extractor_function(domain):
    state = optimizer_workflow.invoke({'domain':domain})
    # print(state['feature_content'])
    return state['feature_content']