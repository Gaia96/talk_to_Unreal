# 07 · Testing and debugging

How to run the project, what a correct run looks like, and how to find the broken link when it is not.

## 7.1 How to run

- Server terminal open and showing `Application startup complete.` ([04](04-python-server.md#43-start-the-server)).
- Unreal: menu next to **Play** → **Standalone Game**. This is the reference mode. *Play In Editor* also works, but the editor captures the mouse (Esc may not release it; use Shift+F1).
- Close the game with **Shift+F1** or by closing its window.
- **Window → Developer Tools → Output Log** shows engine messages and warnings.

## 7.2 Test T1 · server stopped

Stop the server (Ctrl+C in its terminal).

| # | Action | Expected |
|---|---|---|
| 1 | Start Standalone Game | White cube on the floor; dark chat panel bottom left. |
| 2 | Read the chat | `Type a request, for example "make the cube red".` |
| 3 | Type `hello`, Enter | `You: hello`, then `System: The assistant is not responding.` The text box is empty again. |

This exercises **On Request Fail**: nothing listens on port 8000, the connection is refused.

## 7.3 Test T2 · server running

Start the server. In the Unreal game type the sentences below. After each one, look at the chat, the cube and the **server terminal**: every sentence must add a line `POST /query HTTP/1.1" 200 OK`.

| Sentence | Expected chat | Cube |
|---|---|---|
| `make the cube red` | `You: make the cube red` · `System: The cube is now red.` | red |
| `rendi il cubo blu` | `System: The cube is now blue.` | blue |
| `Paint the cube green, please.` | `System: The cube is now green.` | green |
| `set the cube back to white` | `System: The cube is now white.` | white |
| `order me a pizza` | `System: I can't do that here.` | unchanged |
| `make the cube bigger` | `System: I can't do that here.` | unchanged |
| `paint the wall red` | `System: The cube is now red.` | red. A **known false accept** (score 0.62), kept as a discussion case, see [04](04-python-server.md#45-the-evaluation-scripts). |

The chat keeps all lines, in order, and scrolls to the last one.

**The `ambiguous` branch** rarely triggers with this catalog. To test it, stop the server and start it with a margin no answer can reach:

```bash
MARGIN=1.1 python -m uvicorn server:app --host 127.0.0.1 --port 8000     # Linux, macOS
```
```powershell
$env:MARGIN = "1.1"; python -m uvicorn server:app --host 127.0.0.1 --port 8000     # Windows
```

Every sentence that would be `ok` is now `ambiguous`, and the chat must show `System: I'm not sure what you mean, can you rephrase?` with the cube unchanged. Restart the server normally afterwards.

## 7.4 Symptoms and causes

Find the row that matches what you see. The first three rows are the most common, and they all come from a single missing or wrong wire.

| Symptom | Most likely cause | Check |
|---|---|---|
| Typing and Enter does nothing: no `You:` line, no `POST` line in the server terminal | The white output pin of the red `SendQuery` event in `BP_AgentClient` is not wired | 6.3 Step 8.3. Also check the white wire `Set Cube → Bind Event to On Submit` (Step 7) and, in `WBP_Chat`, `Branch.True → Call OnSubmit` (Step 7) |
| `You:` line appears, but no `POST` line and no `System:` line | The chain after `AddLine` is broken before `Process URL` | Part B wires, in order, down to `Process URL` |
| `POST … 200` appears, chat and cube do not change | `OnOk` is not bound, or the `Switch on String` is not wired | Step 12 (white wire into `Bind Event to On Request Complete`), Step 15. Use the Print String probes of 7.5 |
| `System: The assistant is not responding.` while the server runs | Wrong URL; server not finished loading; another program on port 8000; a security tool blocking local connections | `Process URL.URL` is exactly `http://127.0.0.1:8000/query`. Repeat the `curl` test of [05](05-http-get-post.md). The server terminal must show `Application startup complete.` |
| Server terminal shows `422 Unprocessable Entity` | `Set String Field.Field Name` is not exactly `text` | Step 10.5 |
| `System: I can't do that here.` for a sentence that works with `curl` | `Switch on String` pin names or the `status` field name differ (case matters) | Step 15: `status`, `ok`, `ambiguous`, `out_of_scope` |
| Chat says `The cube is now red.` but the cube does not change colour | `ApplyAction` does not get the id, or the material copy does not exist | `Get String Field` has **Field Name** `id`; `Mat` is set in `BP_ColorCube.BeginPlay`; **Parameter Name** is `Color`; only one `BP_ColorCube` in the level (6.2 test) |
| The log shows only the last line, and its first line reads `Txt_Log` | `GetText` missing in `AddLine`: pin 0 of `Format Text` is fed by `Get Txt_Log` directly | 6.1 Step 5.5–5.6 |
| The log is emptied at every new line | `Format Text.Result` is not wired to `Set Text.In Text` | 6.1 Step 5.9 |
| The chat panel covers the whole screen, or *Anchors* is missing in Details | The Border is not inside a Canvas Panel | 6.1 Step 1 (Wrap With… → Canvas Panel) |
| `Input_Text` is wired to **In Text** of `Set Text` through a *To Text (Object)* node | The `Set Text` of another widget was picked (for example the Text Block's) | Delete both nodes and redo 6.1 Step 7.6: **Context Sensitive** unticked, the pink `Set Text` under *Class → Text Box*. If there is no *On Text Committed* event for `Input_Text`, it is probably not a **Text Box** (6.1 Step 2.3) |
| Cannot type in the text box | Focus: `Set Keyboard Focus` missing, or **Clear Keyboard Focus On Commit** is on | 6.1 Steps 4 and 8. If it still does not take keys, in `Set Input Mode UI Only` try **Set Input Mode Game And UI** instead |
| Output Log: *Attempting to focus Non-Focusable widget* | `Chat` is wired into *In Widget to Focus* of `Set Input Mode UI Only` | 6.3 Step 4.3 |
| Compile error *is not a VaRestSubsystem, Target must have a connection* | A request node has no **Target** | 6.3 Step 9.1: add one `Get VaRest Subsystem`, wire it to the Target of `Construct Json Request` and `Construct Json Object` |
| Compile error *is not a TextRenderComponent* | Wrong `Set Text` node (the one of another widget) | 6.1 Step 5.8 |
| A request succeeds but *Get Status* says `Failed_ConnectionError` | Known VaRestX defect on 5.6 | [03](03-varest-plugin.md#a-known-defect-do-not-branch-on-get-status): use only `OnOk` and `OnFail` |
| `Construct Json Request` is not found in the node search | First untick **Context Sensitive** in the search menu (it hides nodes that do not fit the context). If it is still missing: plugin not compiled or not enabled | [03](03-varest-plugin.md#35-open-the-project-and-check-the-plugin) |
| The chat panel never appears, no error | The white chain of `Event BeginPlay` stops before **Add to Viewport** (often **Set Chat** goes straight to **Bind Event to On Submit**) | 6.3 Step 7.3: **Add to Viewport** must have a white wire coming in from **Set Chat**, and **Set Cube** must lead to the Bind node |
| Esc does not stop *Play In Editor* | The viewport captured the mouse | Shift+F1, or use Standalone Game |
| The first sentence after start-up takes about a second longer | Model warm-up in the server | Normal |

## 7.5 Locating a break with Print String probes

When a symptom is not in the table, or the table did not help: put a **Print String** node (text printed top left in the game and in the Output Log) at fixed points. The **first number that does not appear** marks where the chain stops.

For each probe: `from the pin named → add Print String`, type the text in **In String**, and keep the original wiring by sending the Print String's white output to the node that previously followed.

| Where | Text |
|---|---|
| `WBP_Chat`: right after **On Text Committed** | `1 committed` |
| `WBP_Chat`: right after **Call OnSubmit** | `2 submit called` |
| `BP_AgentClient`: right after **Bind Event to On Submit** | `3 bound` |
| `BP_AgentClient`: right after the red **SendQuery** | `4 SendQuery` |
| `BP_AgentClient`: right after **Process URL** | `5 sent` |
| `BP_AgentClient`: first node after **OnOk** | `6 OnOk` |
| `BP_AgentClient`: first node after **OnFail** | `7 OnFail` |

Run, type `make the cube red`, Enter. Reading the result:

- `3` missing at start-up: the chain of Part A stops before `Bind Event to On Submit` (check the wires up to `Set Cube`).
- `1` appears, `2` does not: the Branch with *Commit Method = On Enter* does not fire, or `Call OnSubmit` is not wired to **True**.
- `2` appears, `4` does not: the event is not bound (`3` missing) or the name differs.
- `4` appears, `5` does not: the Part B chain is broken.
- `5` appears, then `7`: the request failed (server, URL).
- `5` appears, then `6`, chat unchanged: the problem is in Part C.

Remove the probes when you are done, then Compile and Save.

## 7.6 Checking the server alone

Whenever Unreal behaves unexpectedly, send the same sentence with `curl` ([05](05-http-get-post.md#53-post)). If the server answers correctly, the problem is on the Unreal side; if not, it is in the server or the catalog. The script `python eval/demo_script.py` (from `server/`) should print `9/9 as expected`.

## 7.7 Definition of done

- [ ] T1: with the server stopped, `System: The assistant is not responding.` and no crash.
- [ ] T2: the four colour sentences change the cube; `order me a pizza` does not.
- [ ] The chat holds all lines, in order.
- [ ] `python eval/demo_script.py` prints `9/9 as expected`.
- [ ] Compile has no errors in `WBP_Chat`, `BP_ColorCube`, `BP_AgentClient`.

Next: [08 · Beyond the base](08-extend.md).
