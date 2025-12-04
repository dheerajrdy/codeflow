"""
Mock tools for context engineering demonstration.

These tools simulate real research/analysis tools but with controllable
output sizes to demonstrate context growth patterns.
"""

import random
from typing import List


def generate_mock_text(word_count: int, topic: str = "general") -> str:
    """Generate mock text of specified length."""
    words = [
        "analysis",
        "research",
        "data",
        "findings",
        "results",
        "insights",
        "metrics",
        "performance",
        "evaluation",
        "assessment",
        "investigation",
        "examination",
        "review",
        "study",
        "report",
        "summary",
        "details",
        "information",
        "statistics",
        "trends",
    ]

    topic_words = {
        "company": [
            "startup",
            "founder",
            "funding",
            "product",
            "revenue",
            "growth",
            "market",
            "customers",
            "team",
            "technology",
        ],
        "financial": [
            "investment",
            "valuation",
            "round",
            "series",
            "investors",
            "capital",
            "equity",
            "returns",
            "profit",
            "revenue",
        ],
        "product": [
            "features",
            "platform",
            "users",
            "interface",
            "technology",
            "innovation",
            "solution",
            "service",
            "offering",
            "capabilities",
        ],
    }

    word_pool = words + topic_words.get(topic, [])
    return " ".join(random.choice(word_pool) for _ in range(word_count))


def search_companies(query: str, max_results: int = 5) -> str:
    """
    Mock search tool - returns list of companies.

    Simulates ~500 tokens of output (roughly 375 words) with ±20% variance.
    """
    companies = [
        "Anthropic",
        "OpenAI",
        "Cohere",
        "Stability AI",
        "Perplexity",
        "Midjourney",
        "Runway",
        "Character.AI",
        "Inflection AI",
        "Adept",
    ]

    results = []
    for i, company in enumerate(companies[:max_results]):
        # Each result: ~75 words with variance (60-90)
        brief_words = random.randint(24, 36)  # 30 ± 20%
        focus_words = random.randint(12, 18)  # 15 ± 20%
        result = f"""
Company {i+1}: {company}
Brief: {generate_mock_text(brief_words, "company")}
Founded: {random.randint(2015, 2023)}
Focus: {generate_mock_text(focus_words, "product")}
Status: {random.choice(['Series A', 'Series B', 'Series C', 'Public'])}
"""
        results.append(result.strip())

    return "\n\n".join(results) + f"\n\nFound {len(results)} companies matching '{query}'"


def get_company_details(company_name: str) -> str:
    """
    Mock company details tool - returns detailed information.

    Simulates ~800 tokens of output (roughly 600 words) with ±15% variance.
    """
    # Add variance to each section (±15%)
    details = f"""
COMPANY PROFILE: {company_name}

OVERVIEW:
{generate_mock_text(random.randint(85, 115), "company")}

FOUNDING STORY:
{generate_mock_text(random.randint(68, 92), "company")}

PRODUCT & TECHNOLOGY:
{generate_mock_text(random.randint(102, 138), "product")}

MARKET POSITION:
{generate_mock_text(random.randint(77, 103), "company")}

TEAM & LEADERSHIP:
{generate_mock_text(random.randint(60, 80), "company")}

KEY ACHIEVEMENTS:
{generate_mock_text(random.randint(68, 92), "company")}

CURRENT STATUS:
{generate_mock_text(random.randint(51, 69), "company")}
"""
    return details.strip()


def get_funding_info(company_name: str) -> str:
    """
    Mock funding information tool.

    Simulates ~600 tokens of output (roughly 450 words) with variance.
    Variable number of rounds (2-5) creates natural variance.
    """
    rounds = []
    total_funding = 0

    # Variable number of rounds creates realistic variance
    num_rounds = random.randint(2, 5)
    for i in range(num_rounds):
        amount = random.randint(5, 100) * 1_000_000
        total_funding += amount
        round_name = ["Seed", "Series A", "Series B", "Series C", "Series D"][i]

        # Vary detail length per round (±20%)
        detail_words = random.randint(32, 48)
        round_info = f"""
{round_name} Round:
Amount: ${amount:,}
Date: {random.randint(2018, 2024)}
Lead Investor: {random.choice(['Sequoia', 'a16z', 'Tiger Global', 'SoftBank', 'GV'])}
Details: {generate_mock_text(detail_words, "financial")}
"""
        rounds.append(round_info.strip())

    summary = f"""
FUNDING SUMMARY: {company_name}

Total Raised: ${total_funding:,}
Number of Rounds: {len(rounds)}

FUNDING ROUNDS:

{"=" * 60}
""" + "\n\n".join(
        rounds
    )

    return summary.strip()


def get_traction_metrics(company_name: str) -> str:
    """
    Mock traction metrics tool.

    Simulates ~500 tokens of output (roughly 375 words) with ±15% variance.
    """
    # Vary detail sections (±15%)
    metrics = f"""
TRACTION METRICS: {company_name}

USER METRICS:
Monthly Active Users: {random.randint(100, 10000)}K
Growth Rate: {random.randint(10, 200)}% YoY
User Retention: {random.randint(60, 95)}%
Details: {generate_mock_text(random.randint(43, 58), "company")}

REVENUE METRICS:
Annual Recurring Revenue: ${random.randint(10, 500)}M
Revenue Growth: {random.randint(50, 300)}% YoY
Average Revenue Per User: ${random.randint(10, 200)}
Details: {generate_mock_text(random.randint(43, 58), "financial")}

ENGAGEMENT METRICS:
Daily Active Users: {random.randint(50, 5000)}K
Session Duration: {random.randint(5, 60)} minutes
Sessions Per User: {random.randint(3, 20)} per week
Details: {generate_mock_text(random.randint(43, 58), "product")}

MARKET METRICS:
Market Share: {random.randint(5, 40)}%
Competitive Position: {random.choice(['Leader', 'Challenger', 'Follower'])}
Geographic Reach: {random.randint(20, 150)} countries
Details: {generate_mock_text(random.randint(43, 58), "company")}
"""
    return metrics.strip()


def analyze_companies(company_data: List[str]) -> str:
    """
    Mock analysis tool - synthesizes multiple company data.

    Simulates ~400 tokens of output (roughly 300 words) with ±15% variance.
    """
    # Vary each section (±15%)
    analysis = f"""
COMPARATIVE ANALYSIS

DATASET: Analyzed {len(company_data)} companies

KEY FINDINGS:
{generate_mock_text(random.randint(68, 92), "company")}

MARKET TRENDS:
{generate_mock_text(random.randint(60, 80), "company")}

COMPETITIVE LANDSCAPE:
{generate_mock_text(random.randint(51, 69), "company")}

INVESTMENT PATTERNS:
{generate_mock_text(random.randint(43, 58), "financial")}

RECOMMENDATIONS:
{generate_mock_text(random.randint(34, 46), "company")}
"""
    return analysis.strip()


def generate_report(analysis_data: str) -> str:
    """
    Mock report generation tool.

    Simulates ~300 tokens of output (roughly 225 words) with ±15% variance.
    """
    # Vary each section (±15%)
    report = f"""
EXECUTIVE SUMMARY REPORT

ANALYSIS SCOPE:
{generate_mock_text(random.randint(34, 46), "company")}

KEY INSIGHTS:
{generate_mock_text(random.randint(51, 69), "company")}

STRATEGIC RECOMMENDATIONS:
{generate_mock_text(random.randint(43, 58), "company")}

RISK ASSESSMENT:
{generate_mock_text(random.randint(34, 46), "financial")}

CONCLUSION:
{generate_mock_text(random.randint(30, 40), "company")}
"""
    return report.strip()


# Tool definitions for agent use
def search_companies_tool(query: str) -> str:
    """Search for AI/ML companies matching the query."""
    return search_companies(query, max_results=5)


def company_details_tool(company_name: str) -> str:
    """Get detailed information about a specific company."""
    return get_company_details(company_name)


def funding_info_tool(company_name: str) -> str:
    """Get funding information for a company."""
    return get_funding_info(company_name)


def traction_metrics_tool(company_name: str) -> str:
    """Get traction and performance metrics for a company."""
    return get_traction_metrics(company_name)


def analyze_tool(data: str) -> str:
    """Analyze company data and generate insights."""
    # Simulate analysis of provided data
    return analyze_companies([data])


def report_tool(analysis: str) -> str:
    """Generate executive summary report from analysis."""
    return generate_report(analysis)
