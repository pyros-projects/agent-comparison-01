# Project: Research Catalog Database

Implement the following functionality in a web application:

A web application that serves as a research catalog database for AI related research papers.

The application should have the following features:

## Cataloguing mode - Papers

The app searches on its own for new interesting research papers from arxiv and other sources, downloads them, and analyzes them via an LLM (gpt-5 on OpenAI/Azure OpenAI).
It summarizes each paper, adds tags, a list of questions the paper answers, and a list of key findings.
It also assigns a real world relevancy score x/10 and an "interesting stuff" score x/10.
All results are saved in a GraphRAG database (for this PoC use something simple like TinyDB and build a graph rag on top of it).
The goal is to make research clusters easy to find and to detect papers that are similar to each other.

## Cataloguing mode - Repositories

The app searches on its own for new interesting research repositories from GitHub and other sources, downloads them, and analyzes them via an LLM (gpt-5 on OpenAI/Azure OpenAI).
It summarizes the repository, adds tags, a list of questions the repository answers, and a list of key findings.
It also assigns a real world relevancy score x/10 and an "interesting stuff" score x/10.
All results are saved in the same database as the papers so that related code can be found easily.

Both modes run indefinitely until the user stops them.

## Search mode

The user can search the database for papers and repositories and view detailed information.
Everything should be nicely presented in a sleek web interface that highlights the most important information and links to the relevant parts of the paper or repository.
The app should also be able to process a link to a paper or repository, analyze it, and find similar papers or repositories.

## Theory mode

The user enters a theory or a question and the app searches the database for papers and repositories related to it.
The interface should show, for example, how many papers agree with the theory, how many disagree, and any other relevant information.

## Views

* Graph view: Graph or cluster visualization of ingested papers and repositories
* Dashboard view: High level overview of the number of papers ingested and other important stats

## Realtime Feedback

* A status bar should always show the state of the system (for example: current ingest progress)

If a search or theory query yields too few results to be useful, the app should suggest related theories or questions that might be more relevant, or suggest starting cataloguing mode to search for more data.

---

## Technical Requirements

* Python backend with uv as project manager (already initialized). Use "uv add" and "uv run" to add dependencies and run the app.
* Web frontend built with Vite + React.
* Use browser tools like Playwright MCP tools to test the frontend.
* Use litellm to communicate with LLMs.
* You may choose to add anything else you find useful to the project.

---

## Compliance/Rules

You are allowed to search the internet for information.
A .env file is provided with DEFAULT_MODEL DEFAULT_EMBEDDING_MODEL and keys to be consumed by litellm. do not overwrite it and use the values it provides.
Do not use interactive commands like some npm scaffolding commands that need user interaction. doin so automatically fails the task.