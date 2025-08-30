import os
import re
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0)


def fetch_website_text(url: str) -> str:
    """Fetch visible text content from a website URL with User-Agent to avoid 403 errors."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texts = soup.stripped_strings
        visible_text = " ".join(texts)
        return visible_text[:3000]  # Truncate if needed
    except Exception as e:
        print(f"Error fetching website content: {e}")
        return ""


def clean_llm_json(text: str) -> str:
    """Remove markdown code fences from LLM JSON output before parsing."""
    cleaned_str = text.replace("```json", "")
    cleaned_str = cleaned_str.replace("```", "")
    return cleaned_str.strip()


def summarize_features_from_website(software_name: str, software_url: str, features: list) -> dict:
    """Generate detailed summaries for features, then generate short summarizers for each feature."""
    website_text = fetch_website_text(software_url)
    features_str = ", ".join(features)

    # Step 1: Get detailed feature descriptions as JSON
    detailed_prompt = f"""
You are a SaaS product analyst. Analyze the following website content for {software_name} ({software_url}).
Focus on these features: {features_str}.
Summarize information related to each feature in a JSON object where keys are feature names and values are detailed descriptions.

Website content:
{website_text}

Return ONLY valid JSON.
"""
    llm_response = llm.invoke(detailed_prompt)
    raw_json = llm_response.content.strip()
    clean_json_str = clean_llm_json(raw_json)

    try:
        detailed_summaries = json.loads(clean_json_str)
    except json.JSONDecodeError:
        print("LLM returned invalid JSON for detailed summaries:")
        print(raw_json)
        detailed_summaries = {feat: "" for feat in features}  # fallback

    # Step 2: For each detailed summary, generate a short summarizer phrase
    result = {}
    for feat, detail_text in detailed_summaries.items():
        summarizer_prompt = f"""
Summarize the following detailed description into a short phrase or keyword:

{detail_text}

Provide ONLY the short summarizer phrase.
"""
        summary_resp = llm.invoke(summarizer_prompt)
        summarizer = summary_resp.content.strip()

        result[feat] = {
            "summarizer": summarizer,
            "details": detail_text
        }

    return result

def llm_agent(domain, software_name, software_url, features, features_desc):
# if __name__ == "__main__":
    # res = [('crm', 'znicrm', 'https://znicrm.com/', ['Scalability', 'Pricing Structure', 'Ease of Implementation', 'User Interface', 'Mobile Accessibility', 'Integration Capabilities', 'Customization Options', 'Contact Management', 'Pipeline Management', 'Automation Features', 'Reporting and Analytics', 'Email Integration', 'Customer Support', 'Data Security', 'Free Trial Period', 'Training Resources', 'Social Media Integration', 'Task Management', 'Document Management', 'API Access'], ['The ability to grow with your business, adding users, data, and functionality without performance degradation or significant cost increases', 'Transparent, predictable pricing that fits startup budgets, ideally with a per-user model and no hidden costs', 'Quick setup process with minimal technical expertise required, allowing for rapid deployment', 'Intuitive, clean design that requires minimal training and encourages team adoption', 'Robust mobile apps or responsive design that allows team members to access and update CRM data from anywhere', 'Pre-built connectors or APIs that allow the CRM to work with other business tools (email, marketing, accounting, etc.)', 'Ability to tailor fields, workflows, and processes to match your specific business needs without coding', 'Comprehensive tools for storing, organizing, and accessing customer information and interaction history', 'Visual sales pipeline tracking with opportunity stages, forecasting, and conversion analytics', 'Tools to automate repetitive tasks, follow-ups, and workflows to increase efficiency', 'Built-in reporting tools with customizable dashboards to track KPIs and business performance', 'Seamless connection with email platforms for tracking communications and enabling templates', 'Quality and availability of vendor support through multiple channels (chat, email, phone)', 'Strong security measures including encryption, compliance certifications, and data backup capabilities', 'Opportunity to test the platform with your team before committing financially', 'Availability of documentation, tutorials, webinars, and other learning materials', 'Ability to connect with and monitor social platforms for customer engagement', 'Features for assigning, tracking, and completing tasks related to customer relationships', 'Storage and organization of customer-related documents, proposals, and contracts', 'Developer tools for custom integrations and extending CRM functionality']), ('crm', 'odoo', 'https://www.odoo.com/', ['Scalability', 'Pricing Structure', 'Ease of Implementation', 'User Interface', 'Mobile Accessibility', 'Integration Capabilities', 'Customization Options', 'Contact Management', 'Pipeline Management', 'Automation Features', 'Reporting and Analytics', 'Email Integration', 'Customer Support', 'Data Security', 'Free Trial Period', 'Training Resources', 'Social Media Integration', 'Task Management', 'Document Management', 'API Access'], ['The ability to grow with your business, adding users, data, and functionality without performance degradation or significant cost increases', 'Transparent, predictable pricing that fits startup budgets, ideally with a per-user model and no hidden costs', 'Quick setup process with minimal technical expertise required, allowing for rapid deployment', 'Intuitive, clean design that requires minimal training and encourages team adoption', 'Robust mobile apps or responsive design that allows team members to access and update CRM data from anywhere', 'Pre-built connectors or APIs that allow the CRM to work with other business tools (email, marketing, accounting, etc.)', 'Ability to tailor fields, workflows, and processes to match your specific business needs without coding', 'Comprehensive tools for storing, organizing, and accessing customer information and interaction history', 'Visual sales pipeline tracking with opportunity stages, forecasting, and conversion analytics', 'Tools to automate repetitive tasks, follow-ups, and workflows to increase efficiency', 'Built-in reporting tools with customizable dashboards to track KPIs and business performance', 'Seamless connection with email platforms for tracking communications and enabling templates', 'Quality and availability of vendor support through multiple channels (chat, email, phone)', 'Strong security measures including encryption, compliance certifications, and data backup capabilities', 'Opportunity to test the platform with your team before committing financially', 'Availability of documentation, tutorials, webinars, and other learning materials', 'Ability to connect with and monitor social platforms for customer engagement', 'Features for assigning, tracking, and completing tasks related to customer relationships', 'Storage and organization of customer-related documents, proposals, and contracts', 'Developer tools for custom integrations and extending CRM functionality'])]
    # domain, software_name, software_link, features
    # for domain, software_name, software_url, features, features_desc  in res:
    # for i in res:
        # print(len(i), end='\n\n\n')
    summary = summarize_features_from_website(software_name, software_url, features)
    print(json.dumps(summary, indent=2), end='\n\n\n\n\n')
    return (json.dumps(summary, indent=2))
        
        # print(software_name, software_url, features)

# Example usage
# if __name__ == "__main__":
#     software_name = "Hostinger"
#     software_url = "https://www.hostinger.com/"
#     features = ["Scalability", "Pricing Model", "Performance"]

#     summary = summarize_features_from_website(software_name, software_url, features)
#     print(json.dumps(summary, indent=2))


# import os
# import re
# import json
# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic

# load_dotenv()

# os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
# llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0)


# def fetch_website_text(url: str) -> str:
#     """Fetch visible text content from a website URL with User-Agent to avoid 403 errors."""
#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                           "AppleWebKit/537.36 (KHTML, like Gecko) "
#                           "Chrome/114.0.0.0 Safari/537.36"
#         }
#         response = requests.get(url, headers=headers, timeout=10)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, "html.parser")
#         texts = soup.stripped_strings
#         visible_text = " ".join(texts)
#         return visible_text[:3000]  # Truncate to avoid too long prompt
#     except Exception as e:
#         print(f"Error fetching website content: {e}")
#         return ""


# def clean_llm_json(text: str) -> str:
#     """Remove markdown code fences from LLM JSON output before parsing."""
#     cleaned_str = text.replace("```json", "")
#     cleaned_str = cleaned_str.replace("```", "")
#     # print(f'fe:{cleaned_str}')
#     # feature_data = json.loads(cleaned_str)
#     return cleaned_str.strip()


# def summarize_features_from_website(software_name: str, software_url: str, features: list) -> dict:
#     """Use LLM to summarize features info from website text, returning JSON dict."""
#     website_text = fetch_website_text(software_url)
#     features_str = ", ".join(features)

#     prompt = f"""
# You are a SaaS product analyst. Analyze the following website content for {software_name} ({software_url}).
# Focus on these features: {features_str}.
# Summarize information related to each feature in a JSON object where keys are feature names and values are summarized content.

# Website content:
# {website_text}

# Return ONLY valid JSON.
# """
#     llm_response = llm.invoke(prompt)
#     raw_json = llm_response.content.strip()
#     clean_json_str = clean_llm_json(raw_json)

#     try:
#         result_json = json.loads(clean_json_str)
#         return result_json
#     except json.JSONDecodeError:
#         print("LLM returned invalid JSON:")
#         print(raw_json)
#         # fallback: return empty summaries
#         return {feat: "" for feat in features}


# # Example usage
# if __name__ == "__main__":
#     software_name = "Hostinger"
#     software_url = "https://www.hostinger.com/"
#     features = ["Scalability", "Pricing Model", "Performance"]

#     summary = summarize_features_from_website(software_name, software_url, features)
#     print(json.dumps(summary, indent=2))
