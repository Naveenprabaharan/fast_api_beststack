import json
import re

json_str = """{
  "hosting_saas_features": [
    {
      "feature": "Scalability",
      "feature_description": "Ability to easily scale resources up or down based on traffic and growth needs without significant downtime or migration efforts"
    },
    {
      "feature": "Reliability & Uptime",
      "feature_description": "Service level agreements (SLAs) guaranteeing high availability (ideally 99.9%+ uptime) with minimal planned downtime"
    },
    {
      "feature": "Performance",
      "feature_description": "Fast load times, global CDN availability, and server response metrics that support your application requirements"
    },
    {
      "feature": "Security Features",
      "feature_description": "Built-in security measures including DDoS protection, SSL/TLS certificates, firewall options, and regular security updates"
    },
    {
      "feature": "Backup & Disaster Recovery",
      "feature_description": "Automated backup systems, point-in-time recovery options, and clear disaster recovery procedures"
    },
    {
      "feature": "Developer Tools",
      "feature_description": "CI/CD integration, staging environments, version control compatibility, and developer-friendly interfaces"
    },
    {
      "feature": "Technical Support",
      "feature_description": "Quality and availability of customer support, including response times, support channels, and technical expertise"
    },
    {
      "feature": "Cost Structure",
      "feature_description": "Transparent pricing, startup-friendly plans, cost predictability, and resource-based pricing that aligns with your growth"
    },
    {
      "feature": "Compliance & Certifications",
      "feature_description": "Relevant industry certifications (SOC 2, GDPR, HIPAA, etc.) that match your regulatory requirements"
    },
    {
      "feature": "Database Options",
      "feature_description": "Support for required database types, managed database services, and database scaling capabilities"
    },
    {
      "feature": "Technology Stack Compatibility",
      "feature_description": "Support for your specific programming languages, frameworks, and technical requirements"
    },
    {
      "feature": "Monitoring & Analytics",
      "feature_description": "Built-in monitoring tools, performance analytics, and observability features to track application health"
    },
    {
      "feature": "Migration Support",
      "feature_description": "Tools and assistance for migrating existing applications or data to the platform"
    },
    {
      "feature": "API Access",
      "feature_description": "Comprehensive API access for automation, integration with other tools, and programmatic control"
    },
    {
      "feature": "Geographic Distribution",
      "feature_description": "Server locations and data center options that match your target market and compliance requirements"
    }
  ]
}"""
# cleaned_str = json_str.replace("```json", "")
# cleaned_str = cleaned_str.replace("```", "")
try:
    data = json.loads(json_str)
    keys_list = list(data.keys())  # convert dict_keys to list
    first_key = keys_list[0]       # get the first key as string
    print(first_key)
except json.JSONDecodeError as e:
    print("JSON decode error:", e)
    print("Cleaned JSON string was:")
    