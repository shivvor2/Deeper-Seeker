# Deeper Seeker

## Overview
The **Deeper seeker** is a simpler OSS version of Deep Research launched by OpenAI. It is a tool designed to perform comprehensive market research, competitor analysis, and investment memo preparation. 

The tool is built to:
- Conduct iterative research with continuous refinement.
- Generate structured search queries and analyze results.
- Produce well-formatted, actionable reports tailored to user queries.

---

![Demo video](public/final_v1.gif)

## Key Features
1. **Iterative Research Workflow:**
   - Plans research steps based on user queries.
   - Generates precise search queries using the Exa API.
   - Continuously refines research based on findings.

2. **Structured Output:**
   - Produces JSON-structured search queries for API calls.
   - Formats search results with highlights, citations, and summaries.

3. **Comprehensive Reporting:**
   - Synthesizes research findings into actionable reports.
   - Includes reasoning, plans, and link counts for transparency.

4. **Customizable Queries:**
   - Handles simple to complex research tasks, including:
     - Market research and sizing.
     - Competitor analysis.
     - Investment memo preparation.

---

## How It Works
1. **User Query:**
   - The user provides a research query (e.g., "Analyze the global EV market in 2024").

2. **Research Planning:**
   - The AI creates a research plan, including reasoning and search queries.

3. **Search Execution:**
   - The tool uses the Exa API to search the web for relevant information.

4. **Result Processing:**
   - Search results are processed, formatted, and analyzed.

5. **Iterative Refinement:**
   - The AI evaluates the results, refines the plan, and performs additional searches if needed.

6. **Final Report:**
   - All findings are synthesized into a comprehensive, well-formatted report.

---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/deep-research-assistant.git
   cd deep-research-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file and add your API keys:
     ```
     EXA_API_KEY=your_exa_api_key
     OPENAI_API_KEY=your_openai_api_key
     ```

---

## Usage
1. Run the script:
   ```bash
   python main.py
   ```

2. Enter your research query when prompted:
   ```
   Enter your query: Analyze the competitive landscape of the cloud computing industry.
   ```

3. View the research process and final report:
   - The tool will display reasoning, plans, search results, and link counts for each iteration.
   - The final report will be printed in the console.

---

## Example Queries
Here are some sample queries to test the tool:
1. **Market Research:**
   - "Provide an overview of the global electric vehicle (EV) market in 2024."
   - "What are the current trends in the plant-based food industry?"

2. **Competitor Analysis:**
   - "Compare Tesla and Rivian in terms of market share and product offerings."
   - "Analyze the competitive landscape of the cloud computing industry."

3. **Investment Memo Prep:**
   - "Prepare a brief investment memo for a fintech startup specializing in blockchain-based payments."
   - "Evaluate the investment potential of the renewable energy sector."

---

## Code Structure
- `main.py`: Main script for running the research assistant.
- `exa_search()`: Function to query the Exa API for search results.
- `generate_research_step()`: Function to create research plans and queries using OpenAI.
- `process_search_results()`: Function to format and analyze search results.
- `ResearchAgent`: Class to manage the iterative research process.

---

## Dependencies
- Python 3.8+
- Libraries:
  - `openai`: For AI-powered reasoning and planning.
  - `requests`: For making API calls to Exa.
  - `colorama`: For colored console output.
  - `pydantic`: For data validation.

---

## Configuration
- **Exa API Key**: Required for web search functionality. Sign up at [Exa AI](https://exa.ai/).
- **OpenAI API Key**: Required for AI reasoning and planning. Sign up at [OpenAI](https://platform.openai.com/).

---

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments
- **Exa AI**: For providing the web search API.
- **OpenAI**: For powering the AI reasoning and planning capabilities.
- **Colorama**: For enhancing console output readability.

---

## Contact
For questions or feedback, please open an issue on GitHub or contact the maintainer at [your.email@example.com].

---

## Future Enhancements
- Add support for additional data sources (e.g., Crunchbase, Statista).
- Implement a web-based interface for easier interaction.
- Enable export of reports in multiple formats (PDF, Markdown, etc.).
- Add advanced analytics and visualization capabilities.

---

Happy researching! 🚀