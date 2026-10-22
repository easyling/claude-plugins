# Easyling skills for Claude

Skills that teach Claude the Easyling processes. They work together with the Easyling MCP server.

| Skill | What it does |
|---|---|
| `onboarding` | Sets up a site in Easyling or prepares a demo: word count and quote, proxy or crest, scope, collecting content, publishing a language, PDFs per language, going live. |
| `linguistic-quality` | Improves the wording of translations: glossary, terminology, translation memory, styleguide, tone and formality, AI translation, ContentGuard, review. |
| `translate-docx` | Translates a Word document (.docx) with Easyling and keeps its formatting; checks the translated file. |

## Connect the MCP server

Open the AI dialog in the Easyling dashboard (the robot icon in the header). It gives the
connection details for your installation.

- **Claude Code:** the "Claude Code" tab gives the command. It has the form
  `claude mcp add --transport http --scope user easyling <your installation's /_el/ext/mcp URL>`.
- **claude.ai and Claude Desktop:** the "claude.ai and Claude Desktop" tab gives the steps to add
  the custom connector.

In Claude Code you sign in with `/mcp`; on claude.ai the connector asks you to sign in when you
connect it.

## Install the skills

**Claude Code:**

```
claude plugin marketplace add easyling/claude-plugins
claude plugin install easyling@easyling
```

To pick up new versions: `claude plugin marketplace update easyling`.

**claude.ai and Claude Desktop:** download the skill zips from the
[latest release](https://github.com/easyling/claude-plugins/releases/latest) and upload each one
under Customize, Skills:

- [onboarding.zip](https://github.com/easyling/claude-plugins/releases/latest/download/onboarding.zip)
- [linguistic-quality.zip](https://github.com/easyling/claude-plugins/releases/latest/download/linguistic-quality.zip)
- [translate-docx.zip](https://github.com/easyling/claude-plugins/releases/latest/download/translate-docx.zip)
