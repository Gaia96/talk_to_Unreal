# 08 · Beyond the base

## What this guide gives you, and what it does not

You now have a **working base**: a chat in Unreal sends a sentence to a program outside Unreal, which answers with an action that Unreal carries out. It shows one way to build that connection, tested end to end on one machine.

It is a starting point, not a finished project. A group that only reproduces it has not yet done its project: what you add, change and *can explain and justify* is what counts. Nothing here is a recipe for the final work, and none of the ideas below were tested for this guide.

**Nothing in the base is compulsory.**

- **VaRestX** is the way this guide sends HTTP requests from Blueprints. If you find another way that works for you (a different plugin, Unreal's own HTTP module in C++, another protocol), use it.
- **The server and its models** are one way to decide what a sentence means. A language model, a classifier you train, plain rules or something else can take their place.
- **The cube** is a placeholder scenario. Choose your own scene, objects and actions.

What you should keep is the habit the base follows: a clear interface between the parts, a way to test each part on its own, and results you can show.

## What can be swapped

The two sides share only the JSON message of [00](00-overview.md#the-message-contract). Unreal sends a sentence and reads `status`, `id` and `reply`. Anything that keeps that contract can replace the server without touching Unreal, and anything that consumes `id` can replace the cube.

| Part | In the base | Could be replaced by (ideas) |
|---|---|---|
| Scenario | one cube, four colours | your own scene: other objects, other actions, a robot or a simulation, a small game |
| Decision step | retrieval over a hand-written catalog (two models) | a language model that picks an action from a list, a classifier trained on your examples, rules, or a mix |
| Link Unreal ↔ server | VaRestX over HTTP, on `127.0.0.1` | another plugin or C++, another protocol, a server on another machine |
| Input | typed text in a 2D widget | voice, a VR interface, buttons plus text |
| Dialogue | one independent request per sentence | follow-ups (`now make it blue`), with the history kept on the server |
| Models | `multilingual-e5-large` and `bge-reranker-v2-m3` | other models, other sizes, other languages |

## Ideas and warnings

- **Keep a safe boundary.** In the base, free text never reaches the controlled object: only an `id` from a fixed list does. If you put a generative model in the decision step, check that the `id` it returns is in the list before sending it, and map anything else to `out_of_scope`. The same applies if the cube becomes a robot (real or simulated): map `id` to a whitelist of commands, check preconditions, report the outcome in the chat.
- **VR.** The chat of this guide is a 2D widget added to the viewport, which a headset does not render. In VR the widget would have to live in the world (a *Widget Component* on an actor) with a pointer to interact with it, or the sentence would have to come from voice.
- **State.** To let the server answer questions about the scene, Unreal has to send the relevant state (more fields in the JSON body).
- **Another machine.** `127.0.0.1` works because the server and Unreal run on the same computer. For a build on another device, `Process URL` needs the server's network address and the server has to listen on it (`--host 0.0.0.0`); on Android-based devices plain `http` may be blocked by default. Opening the server to a network also exposes it to that network: add authentication before you do.

## Adding an action (the smallest change)

This is the simplest extension and shows the three places an action touches. It was worked out from the code, not run.

1. **Catalog** (`server/catalog/catalog.json`): a new entry with a unique `id`, a `title`, several `descriptions` (in the languages you want to accept), `params` and a `reply`. Restart the server: the catalog is embedded once at start-up. `/health` must show a larger `entries`.

   ```json
   {
     "id": "cube_yellow",
     "title": "cube yellow",
     "descriptions": ["make the cube yellow", "paint the cube yellow", "rendi il cubo giallo"],
     "params": { "color": "yellow" },
     "reply": "The cube is now yellow."
   }
   ```

2. **`BP_ColorCube.ApplyAction`**: in *Switch on String* add the pin name `cube_yellow`, copy one of the existing `Get Mat → Set Vector Parameter Value` pairs, wire it to the new pin and set **Value** to R 1, G 1, B 0.
3. **Test**: send the new sentences with `curl` ([05](05-http-get-post.md)), then in Unreal. Add sentences that must *not* match (`paint the wall yellow`).

Near-identical actions (`on` / `off`, `open` / `close`) should be separate entries, each with its own descriptions.

## Measuring what you build

- `T_ACCEPT` and `MARGIN` ([04](04-python-server.md#41-what-it-does)) are inherited defaults, not tuned values. Tune them on a **development** set and report on a separate **test** set, ideally written by someone who did not write the catalog.
- `server/eval/testset.json` has the format `{"q": "...", "gold": "cube_red" | null}`, and `python eval/run_eval.py` prints accepted and refused counts and latency. Decide what matters for your use: a false accept (acting on a request that should have been refused) usually costs more than a false reject.
- The known false accept `paint the wall red` is a good first problem. Each fix (more catalog entries, more specific descriptions, a higher `T_ACCEPT`) has a cost on the other cases: measure it.

## If you get stuck

1. Go back to the checks of [07](07-test-and-debug.md): the symptom table, the Print String probes, and `curl` against the server alone. Most problems are one missing wire or one wrong name.
2. Make the **smallest change** that could work, test it, and only then make the next one. Changing several things at once makes failures impossible to locate.
3. Keep a copy of the working base (for example a Git commit) so that you can always return to it.
