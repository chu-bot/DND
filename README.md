
**6/28:**

Focusing on Dynamic / Existing AI Actions and the decision-making process, `ai_prompts`, `ai_tools`, and `ai_actions`

* Automatic Work So Far (3:32 PM) - Refactored AI prompts tool. Previously, dynamic actions lived in ai_actions and was clogging the file. Redistributed code, so system prompts now live in ai_prompts. Additionally, reconfigured decision + dynamic_action_creater to use function calling.


* Manual Work - Going through and thinking about AI actions in depth
 -> decision #1: strategy_decision — `strategy_decision` should decide if there are existing primitives which an action could conform to (e.g. pick up a stick can add an item to your inventory w/ existing primitives), or if the general `action` primitive should be used (break open a door).
    * side-note: not sure if `existing actions` or `dynamic actions` is the right title to give things.
    * existing primitive: tool use with a list of primitives, let the AI pick the most fitting primitive and generate new info (might be difficult for primitives w/ others in sub-fields)
    * new action needed: "tool use" with only one tool, defining the action primitive. 
 -> decision #2: name_tbd - should the player be allowed to do this? Increasing a level or granting an item is a fitting primitive, but would disrupt immersion + ruin difficulty and player experience.

side-note: how to handle changes in existing state? Is that a third decision? Like if I punch the innkeeper who gives me the quest, then naturally he won't want to give me the quest anymore. How do we expose the state?

In which order should we figure this out? My two-cents is decision #2 first, because a NO would mean that decision #1 doesn't need to run. However, 3 function calls would need to run each time a player wanted to perform an action like this, which might get expensive fast. 


Other bytes to do:
 -> clunky naming system, not immediately obvious which prompt corresponds to what (IDEK what `suggestion_prompt` corresponds to)
 -> go through system prompts, consolidate info that all share, analyze resources, impact, few-shot examples
 -> Figure out how game_state interfaces with prompt outputs
 -> build out suite of tests
 -> start work on personal AI commandments
 -> extension list for Mom+Dad, configure Ruff + figure out best extensions
 -> get a markdown extension
 -> refactor suggestions, change engine w/ case-by-case logic
     -> suggestion should return not only the action w/ primitives filled-out, but also a description of what occurs (or the trigger to the primitive if that's what is happening)
 -> try and find a dnd skillbook/book that we can scrape

 **7/2**

 * Conversation Primitive
  -> Currently, we have a dialogue and conversation primitive. Each NPC has ONLY ONE associated conversation currently, which limits potential AI people responses. Conersation + dialogue primitives are not the right way to go about this. How to balance hardcode + AI responses?
  -> Potential: 3-4 conversation starters detailing hard-coded answers, one chance to have the conversation thread, otherwise the NPC mentions the repeated nature (maybe 2 for quests)
    -> New topics will be stored as a new conversation path, and categorized into essential/non-essential based on how much it can change the story (if the NPC talks about a potential new location that was their hometown, and how to get there, that's essential. Mentioning what they had for dinner last night is probably less so)
    -> let the AI choose 1) how close a question is to an existing thread, in which case it denies the option to talk. Otherwise, it will create a new conversation thread
    -> 2) essential, non-essential. If it's essential, then we modify / add data to the adventure creating that option
    -> give the AI an extremely high temperature
    -> add a temperament / likeability to player field to the `Player` type, and add a max # of questions you can ask in addition to the pre-set paths.

side-note: Figure out how the AI can modify existing data within the gamestate - get dad's two cents on this?