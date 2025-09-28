# Page snapshot

```yaml
- heading "Workspaces" [level=2]
- button "New workspace"
- button "Collapse tabs"
- text: Workspace 1
- button "Close workspace"
- text: Untitled
- button "Close workspace"
- heading "Workspace" [level=2]
- button
- tablist:
  - tab "Tasks (0)" [selected]
  - tab "Files (0)"
- tabpanel "Tasks (0)":
  - paragraph: No tasks yet
- heading "Deep Agents" [level=1]
- button
- button
- paragraph: ask me what my birthday is
- text: ❓ What is your birthday?
- button "Expand"
- textbox "Type your answer (Enter to send, Shift+Enter for new line)...": March 12, 1990
- button "Send answer"
- text: Working...
- textbox "Type your message..." [disabled]
- button "Stop"
- region "Notifications alt+T"
- alert
```