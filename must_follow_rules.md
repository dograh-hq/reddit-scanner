<system_context>
You must follow all these rules when writing code and also create strutured and nested CLAUDE.md based on these rules.
</system_context>

<important_notes>
## MISSION CRITICAL RULES

1. **Code with elegance and minimalist code** - Write clean, maintainable, and elegant code that follows established patterns. DO not write any extra code- write minimal code instead of trying to cover everything . You dont have to exhaustive in coding. MINIMAL CODE PLEASE> 


2. **User runs the application** - Unless you are running a QA command, you do not run the app. Always ask the user to run the app and report results back to you.

5. **Clarify ambiguity** - Favor asking follow-up questions to ensure clear understanding of requirements before implementation.

6. **Preserve existing functionality** - NEVER reduce the scope of existing features/behaviors unless explicitly instructed to do so.

7. **keep updating all CLAUDE.md files** - it is a living documentation
 - ULTRA CRITICAL: Treat all CLAUDE.md files as living API documentation for your future self. Always check for relevant CLAUDE.md files and update them when changes impact their accuracy.

8. **Writing expert CLAUDE.md files** - Follow the structured format below for clarity and effectiveness. 
</important_notes>

<claude_md_best_practices>
## CLAUDE.MD BEST PRACTICES

### Purpose & Philosophy
- **Living brain**: CLAUDE.md files are your persistent memory across sessions
- **API documentation**: Write for your future self as an expert coding agent
- **Token-aware**: Keep concise while preserving critical information
- **Current state only**: Document what IS, not what WAS (no changelogs)

### Structure & Format

#### 1. XML-Style Tags (Semantic Sections)
```markdown
<system_context>
Brief overview of what this module/system does. Set the stage for understanding.
</system_context>

<file_map>
## FILE MAP
- `/path/to/file` - Brief description
- `/path/to/folder/` - What's in this folder
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)
The canonical way to do things. Battle-tested patterns that MUST be followed.
</paved_path>


<critical_notes>
## CRITICAL NOTES
- **Bold key points** with brief explanations
- Gotchas and edge cases
- Things that will break if done wrong
</critical_notes>
```

####Here are some tags to use
• <system_context> — overview and purpose
• <critical_notes> — must-know information
• <file_map> — where to find things
• <example> — examples and code patterns
• <workflow> — for chain of thought steps
- <must_follow_rules> — mission critical rules


<must_follow_rules>
## MISSION CRITICAL RULES
1. **Code with elegance** - Write clean and minimal code. Do not write anything extra or extra fetures.
2. **Clarify ambiguity** - Favor asking follow-up questions to ensure clear understanding of requirements before implementation.
3. **Preserve existing functionality** - NEVER reduce the scope of existing features/behaviors unless explicitly instructed to do so.
4. **create nested CLAUDE.md**
 - ULTRA CRITICAL: cladue.md files shall be created in every folder and subfolder where you have written any code. It should contain an updated context and overview of the code in that subfolder. Keep updating it if any code changes are made. 
5. **keep updating all CLAUDE.md files- it is a living documentation**
 - ULTRA CRITICAL: Treat all CLAUDE.md files as living API documentation for your future self. Always check for relevant CLAUDE.md files and DEFINITELY UPDATE them when changes impact their accuracy.
6. **Add good comments everywhere** -  add comments in your code to make it better documented. definitely add a one line comment in each file saying what it does and another comment on each function or class saying what it does. when using  external functions and  external libraries , then add a small 4-5 word comment on what it does as well
7. **Output user's next steps and testing instructions** -at every step make sure to output the next steps for the user like adding details in env file or setting up a supabase account etc.  And also share clear instructions on how the user can test the work so far.
8. **Write minimal code** -at every step make sure to write as little code as possible, do not write code for the sake of writing and defeintely dont write a lit of code - only write code thats enough to serve the given use case.
9.  **NEVER use `any` types** - Request user approval if tempted
10. **Update on change** - If code changes affect docs, update immediately- update and create claude.md for folders and subfolders. also update readme.md for context and any updates. When making updates , remove any old context that got changed.
11. **Maintain CHANGES.md** :- maintain a changes.md where you keep logging in the changes you make along with the reason why 
</must_follow_rules>