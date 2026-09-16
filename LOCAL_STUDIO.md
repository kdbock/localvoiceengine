# New Local Studio

This is the local-only version of the new Local Voice Engine design. It does
not sign in to Firebase, call cPanel, or require an API key.

## Open it on a Mac

Double-click `Start New Local Voice Studio.command`. Keep the Terminal window
open while using the studio. The studio opens at `http://127.0.0.1:5173`.

## What is local today

- The story desk and editable storyboard.
- The six brand workspaces and their design assets.
- A Kristy/BJ working-as selector and a local activity log.
- Local package status, stored in that Mac's browser storage.

## GitHub workflow

Both Kristy and BJ should work from their own clone of the repository. Pull
changes before starting work, then commit and push only the files you changed.
The code and templates are shared through GitHub; each Mac keeps its own local
in-progress packages until we connect the new interface to the shared local
render queue.

## Next local build step

Connect this storyboard interface to the existing local Qwen render worker.
That requires the selected Mac to have the approved Qwen model, voice assets,
and video tools installed locally. It makes the final voice and MP4 on that Mac
without sending narration to a paid API.
