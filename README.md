
**6/28:**

Focusing on Dynamic / Existing AI Actions and the decision-making process, `ai_prompts`, `ai_tools`, and `ai_actions`

* Automatic Work So Far (3:32 PM) - Refactored AI prompts tool. Previously, dynamic actions lived in ai_actions and was clogging the file. Redistributed code, so system prompts now live in ai_prompts. Additionally, reconfigured decision + dynamic_action_creater to use function calling.


* Manual Work - Going through and thinking about AI actions in depth
 -> decision #1: strategy_decision — `strategy_decision` should decide if there are existing primitives which an action could conform to (e.g. pick up a stick can add an item to your inventory w/ existing primitives), or if the general `action` primitive should be used (break open a door).
    * side-note: not sure if `existing actions` or `dynamic actions` is the right title to give things.
    * existing primitive: tool use with a list of primitives, let the AI pick the most fitting primitive and generate new info (might be difficult for primitives w/ others in sub-fields)
    * new action needed: "tool use" with only one tool, defining the action primitive. 
 -> decision #2: name_tbd - should the player be allowed to do this? Increasing a level or granting an item is a fitting primitive, but would disrupt immersion + ruin difficulty and player experience.

In which order should we figure this out? My two-cents is decision #2 first, because a NO would mean that decision #1 doesn't need to run. However, 3 function calls would need to run each time a player wanted to perform an action like this, which might get expensive fast. 


Other bytes to do:
 -> clunky naming system, not immediately obvious which prompt corresponds to what (IDEK what `suggestion_prompt` corresponds to)
 -> go through system prompts, consolidate info that all share, analyze resources, impact, few-shot examples
 -> Figure out how game_state interfaces with prompt outputs
 -> build out suite of tests
 -> start work on personal AI commandments
 -> extension list for Mom+Dad, configure Ruff + figure out best extensions
 -> get a markdown extension