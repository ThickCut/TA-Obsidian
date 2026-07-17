# Obsidian Git askpass for Windows
# Relies on Git Credential Manager instead of custom prompt
param([string]$prompt)

# Let Git Credential Manager handle it
$env:GIT_TERMINAL_PROMPT = "0"
exit 0
