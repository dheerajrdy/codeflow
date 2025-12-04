# Interactive Notebooks

These Jupyter notebooks provide interactive, browser-based introductions to PicoAgents concepts. Perfect for learning without local installation!

## 📚 Available Notebooks

| Notebook | Chapter | Topic | Open in Colab |
|----------|---------|-------|---------------|
| [`01_basic_agent.ipynb`](01_basic_agent.ipynb) | Ch 4 | Creating agents with tools | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/victordibia/designing-multiagent-systems/blob/main/examples/notebooks/01_basic_agent.ipynb) |

**More notebooks coming soon!** In the meantime, all examples are available as [Python scripts](../agents/) or try [GitHub Codespaces](../../README.md#getting-started) for the full environment.

## 🚀 Quick Start

### Option 1: Google Colab (Recommended for Beginners)
Click any "Open in Colab" badge above. No installation needed!

**In Colab:**
1. Click the badge to open the notebook
2. Add your OpenAI API key when prompted
3. Run cells with Shift+Enter

### Option 2: Local Jupyter
```bash
# Install Jupyter
pip install jupyter

# Launch notebooks
jupyter notebook examples/notebooks/
```

### Option 3: VS Code
Open any `.ipynb` file in VS Code with the Jupyter extension installed.

## 💡 Tips

- **API Keys**: Use [Colab Secrets](https://x.com/GoogleColab/status/1719798406195867814) to store your OpenAI API key securely
- **GPU**: Most examples don't need GPU, but you can enable it in Colab: Runtime → Change runtime type → GPU
- **Saving**: Colab auto-saves to your Google Drive, or download with File → Download → Download .ipynb

## 🔗 Related Resources

- [Full Python Examples](../agents/) - All examples as Python scripts
- [GitHub Codespaces](../../README.md#getting-started) - Full development environment
- [Book](https://buy.multiagentbook.com) - Complete guide to multi-agent systems
