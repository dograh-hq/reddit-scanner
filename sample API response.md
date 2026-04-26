# SAMPLE  REDDIT SCRAPING API call against url
curl -X POST "https://api.apify.com/v2/acts/fatihtahta~reddit-scraper-search-fast/run-sync-get-dataset-items?token=<YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"includeNsfw":false,"maxComments":1,"maxPosts":10,"scrapeComments":false,"urls":["https://www.reddit.com/r/AI_Agents/top/?t=day"]}'
# SAMPLE  REDDIT SCRAPING API call against Keyword
  curl -X POST "https://api.apify.com/v2/acts/TwqHBuZZPHJxiQrTU/runs?token=<YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"queries":["voice ai"],"sort":"top","timeframe":"week","maxPosts":10,"maxComments":1,"scrapeComments":false,"includeNsfw":false}'

# SAMPLE RESPONSE FROM REDDIT SCRAPING API WHEN SCRAPING FROM A URL (e.g. "https://www.reddit.com/r/AI_Agents/top/?t=day")

[
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3kc7s",
    "title": "Stop burning money sending JSON to your agents.",
    "body": "I've been building agents for a while now as a freelancer, and there's this silent budget killer that nobody talks about. You're paying for punctuation.\n\nEvery time you send a JSON payload to an LLM, you're getting charged for every single brace, bracket, quote, and comma. And if you're sending lists of stuff, like user records, product catalogs, or transaction histories, you're repeating the same field names over and over.\n\n\"id\": 1, \"name\": \"Alice\"... \"id\": 2, \"name\": \"Bob\"...\n\nIt's wasteful. And frankly, it's kind of dumb when you're doing it at scale.\n\nI started messing around with this thing called TOON (Token-Oriented Object Notation) recently. It’s basically JSON on a diet. It strips out all the noise and structures data more like a table.\n\nInstead of repeating \"id\" and \"name\" fifty times, you define the header once and then just list the values. Clean. Simple.\n\nI ran a test on a support agent I'm building. We were feeding it customer order history. Switching from JSON to TOON cut the token count by like 45%.\n\nForty five percent.\n\nThat's almost half the cost gone, just by changing how we format the text.\n\nAnd the crazy part? The models actually seem to prefer it. I think because there's less noise, they hallucinate less on the structure. GPT-4 had zero issues parsing it.\n\nIf you're just sending a couple of fields, stick with JSON. It's fine. But if you're building RAG pipelines or agents that process heavy structured data, you are literally setting money on fire by not optimizing your format.\n\nIt’s a small tweak. But when you're running thousands of calls a day, those brackets add up fast.\n\nWorth a look if you care about your margins.\n\nAnyone else playing with this? Or are we all still married to curly braces?",
    "author": "Warm-Reaction-456",
    "score": 364,
    "upvote_ratio": 0.8,
    "num_comments": 121,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T04:40:12.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3kc7s/stop_burning_money_sending_json_to_your_agents/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3m0ni",
    "title": "LangGraph vs CrewAI for Customer Support AI Agents: Which one is better for real tool-calling workflows?",
    "body": "I’m building a customer-support AI agent that needs **real tool calling**, not just chat.\n\nTypical workflows:\n\n* Fetching **order status**\n* **Rescheduling** an order\n* Pulling **pricing info**\n* Triggering backend APIs\n* Multi-step flows with memory & error handling\n\nI’m trying to decide between **LangGraph** and **CrewAI** for this.\n\nFrom your experience:\n\n* Which one handles structured tool-calling more reliably?\n* How do they behave in real production-like workflows?\n* Any issues with state management, retries, or deterministic execution?\n* Is one clearly better for long-running support flows vs short tasks?\n\nWould love to hear what others have built and what worked (or didn’t).  \n",
    "author": "Federal-Song-2940",
    "score": 7,
    "upvote_ratio": 1,
    "num_comments": 15,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T06:14:22.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3m0ni/langgraph_vs_crewai_for_customer_support_ai/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3k6au",
    "title": "so… i’m teaching ppl how to build an ai browser in 48 hrs 😅",
    "body": "hey guys, so uh… i wasn’t really planning to post this here but a bunch of ppl have been dm’ing me abt it so here goes 😅\n\ni’m hosting this 2-day thing where we actually build an ai web browser from scratch. like… a real one. not a tutorial, not theory, not “here’s the idea,” but actually shipping it.\n\n  \nimagine comet but you made it.\n\ni’ve been building ai stuff nonstop at my startup Aro Labs this year and figured it’s time to give back a bit. so yea, i put together this small workshop called no cap ai.\n\nit’s basically a 48hr sprint where we go thru the whole architechture (yes i spelled that wrong lol) and wire everything up.\n\nno fluff, no bs, no upsells, just real building.\n\nstudents, working ppl, founders… whoever wants to learn how to actually ship ai products instead of watching yt vids all day.\n\nif u want the link/info just drop a comment or dm me and i’ll send it over. 😅🙏\n\nalso making a tiny free community for builders across the country, so if ur into that kinda vibe, i can add u too.\n\nok that’s it, posting this before i overthink it lol.",
    "author": "bhadweshwar",
    "score": 4,
    "upvote_ratio": 0.56,
    "num_comments": 34,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T04:31:16.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3k6au/so_im_teaching_ppl_how_to_build_an_ai_browser_in/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3mv9y",
    "title": "Validated the \"AI Context Switching\" pain point. I’m building the \"Universal Memory OS\" with a hyper-efficient architecture. The dilemma: Bootstrapping slow vs. Raising Seed for velocity.",
    "body": " \nHi everyone,\nLast Time, I validated a critical pain point among power users across multiple communities: \"Context Rot.\"\nWe move between Claude for coding, ChatGPT for reasoning, and Gemini for large documents. But the context is trapped in silos. We waste hours re-explaining things to AI.\n\nThe market signal was clear: Build a solution that unifies memory across these silos without compromising privacy.\n\nI am building DataBuks, and I need strategic advice on financing the next phase.\nThe Vision: The \"AI Memory Operating System\"\nDataBuks isn't just a simple browser extension. It is designed as a two-part ecosystem:\n\n1. The Bridge (Browser Extension):\n\nNative Slash Commands: Stay in the flow. Type /save [project] in ChatGPT. Type /load [project] in Claude to inject context instantly, preserving code blocks and formatting.\nLocal-First Engine: It primarily uses browser storage for data capture, ensuring speed and privacy.\n\n2. The Command Center (Web App Dashboard) — Critical Component\n\nVisual Memory Management: A React-based dashboard to view, organize, tag, and manage your saved context blocks. Think of it as a \"file manager for your second brain.\"\n\nThe Financial Edge & The Dilemma\nI have engineered a \"Local-First, Hyper-Efficient Architecture.\" Because the core data processing happens on the client-side, my marginal infrastructure costs are near zero.\nThis means almost every dollar of revenue goes straight to profit (High Margins).\nThis creates a strategic conflict:\nThe Bootstrapping Path:\n\nI can build the MVP myself using AI-assisted tools with minimal burn rate.\nI retain full control and validate willingness-to-pay before taking outside money.\nRisk: It will be slow.\n\nThe VC/Seed Funding Path (e.g., raising $250k-$500k):\n\nPure Velocity: Since I don't need money for servers, 100% of the funding would go into hiring devs to ship the full ecosystem faster and aggressive go-to-market.\nEnterprise Features: Building secure team sync and integrations (n8n/Make) requires resources to capture the B2B market before platform sherlocking happens.\n\nMy Question to experienced founders:\nWhen you have a validated, high-margin product architecture in a massive market (AI), is bootstrapping a mistake? Should I leverage this efficiency to raise a seed round purely for speed and market capture?\nI’m currently building the MVP. Journey\nThanks for the insight.",
    "author": "No_Jury_7739",
    "score": 5,
    "upvote_ratio": 0.86,
    "num_comments": 7,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T07:05:58.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3mv9y/validated_the_ai_context_switching_pain_point_im/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "https://www.reddit.com/r/AI_Agents/top/?t=day",
    "id": "1p3iisl",
    "title": "Building an AI consultant. Which framework to use? I am a non dev but can code a bit. Heavily dependent on cursor. Looking for a framework 1. production grade 2. great observability for debugging 3. great ease of modifying multi agent orchestration based on feedback",
    "body": "Hi All\n\nI am building an AI consultant. I am wondering which framework to use? \n\nConstraints: \n\n1. I am a non dev but can code a bit. I am heavily dependent on cursor. So any framework which cursor or it's underlying llms are comfortable with. \n\n2. Looking for a framework which can be used for production grade application (planning to refactor current code base and launch the product in a month) \n\n3. Great observability can help with debugging as I understand. So the framework should enable me on this front. \n\n4. Modifying multi agent orchestration based on market feedback should be easy.  \n\nContext: \n\nI have build a version of the application without any framework. However, I just went through a google ADK course in kaggle and after that I realised frameworks could help a lot with building iterating and debugging multi agent scenarios. The application in current form takes a little toll whenever I go on to modifying (may be I am not a developer developer). Hence thought should I give frameworks a try. \n\nAbsolute Critical: \n\nIt's extremely important for me to be able to iterate the orchestration fast to reach PMF fast. ",
    "author": "Technical-Sort-8643",
    "score": 2,
    "upvote_ratio": 1,
    "num_comments": 7,
    "subreddit": "AI_Agents",
    "created_utc": "2025-11-22T03:05:46.000Z",
    "url": "https://www.reddit.com/r/AI_Agents/comments/1p3iisl/building_an_ai_consultant_which_framework_to_use/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.AI_Agents",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  }
]




# SAMPLE RESPONSE FROM REDDIT SCRAPING API WHEN SCRAPING FOR A KEYWORD (e.g. voice ai)
[
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1ozgbht",
    "title": "Teacher messed up our attendance and now it’s “already uploaded” so we’re stuck",
    "body": "I’m so frustrated. Our teacher started using this AI voice thing to take attendance, and it messed up half the class. She marked people absent who were literally right there, mixed up names, said the wrong roll numbers and everything that she could do wrong.\n\nAfter seeing this doc, we confronted her and she just kept saying, “Oh, Wispr must’ve heard it wrong.”\nYes but she was the one using it. Like at least check it before finalizing it??\n\nThe worst part is that this is our final semester and she says it’s already uploaded on the portal, so she “can’t do anything now.”\nSo all of us who were present are actually finally marked absent for no reason, and now instead of studying for the finals, we have to deal with this mess first and have to run around trying to get it corrected😭\n\nIt’s honestly so annoying. Tech is fine, but if you’re relying on it, at least double-check things instead of blaming the app and leaving us with the mess. And we're not even sure if she is still going to stop using it or not.",
    "author": "alookitikki",
    "score": 6700,
    "upvote_ratio": 0.97,
    "num_comments": 156,
    "subreddit": "mildlyinfuriating",
    "created_utc": "2025-11-17T13:30:28.000Z",
    "url": "https://www.reddit.com/r/mildlyinfuriating/comments/1ozgbht/teacher_messed_up_our_attendance_and_now_its/",
    "flair": null,
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "i.redd.it",
    "thumbnail": "https://b.thumbs.redditmedia.com/7Ry2XR7yhZXt0HIbcqIGP2jnX0h6g0F4GBSLcd6DqgA.jpg",
    "url_overridden_by_dest": "https://i.redd.it/g01algplkt1g1.jpeg",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p2ynlu",
    "title": "Frank dropped a Statement about the AI usage in Brawl Stars",
    "body": "",
    "author": "Exciting-Year-2343",
    "score": 2857,
    "upvote_ratio": 0.98,
    "num_comments": 302,
    "subreddit": "Brawlstars",
    "created_utc": "2025-11-21T13:30:36.000Z",
    "url": "https://www.reddit.com/r/Brawlstars/comments/1p2ynlu/frank_dropped_a_statement_about_the_ai_usage_in/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "i.redd.it",
    "thumbnail": "https://b.thumbs.redditmedia.com/gQ_z0I9qw8m5b8AqC_bLPZSIn1d7IxRvelajoWqkCLY.jpg",
    "url_overridden_by_dest": "https://i.redd.it/945w0lt94m2g1.png",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p2fz4k",
    "title": "We NEED to mass uninstall",
    "body": "Generative AI? SERIOUSLY? \"Oh, b- but, is just a Dev Tool to make their work easier!\" Look at the image they presented, is Al This is just the beginning, and if we let THIS slide. It's over\n\nSupercell is a soulless company, I hate that amazing artists and passionate people now need to work for the money hungry CEOs at the top, but we need to do SOMETHING\n\nMASS UNINSTALL, not only Brawl Stars, CC, CR, SQ, MOCO, BB, HD EVERYTHING\n\nThey NEED to hear us, WE are the players, WE made them popular, they're not too big to fail, they need us\n\nThis is our last chance before the point of no return, so PLEASE, everyone I'm not asking to delete our accounts because the objective is to come back to the game, with a better Supercell But we need to show our voices, show our revolt, and because our words and pleads aren't enough, we hurt them at their Wallets We hurt them at their numbers of players\n\nSo please, everyone who ever liked Supercell and the games they made, and show our anger at Al together",
    "author": "Shy_L",
    "score": 1918,
    "upvote_ratio": 0.86,
    "num_comments": 390,
    "subreddit": "Brawlstars",
    "created_utc": "2025-11-20T21:39:11.000Z",
    "url": "https://www.reddit.com/r/Brawlstars/comments/1p2fz4k/we_need_to_mass_uninstall/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "old.reddit.com",
    "thumbnail": "https://b.thumbs.redditmedia.com/wkVJtoI44MPvJ9RErO3M3eQAlypWO2SOXB9Isvcadqs.jpg",
    "url_overridden_by_dest": "https://www.reddit.com/gallery/1p2fz4k",
    "media": null,
    "media_metadata": {
      "m6ezu85jeh2g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 193,
            "x": 108,
            "u": "https://preview.redd.it/m6ezu85jeh2g1.jpg?width=108&crop=smart&auto=webp&s=c721597168d2ae4f79bdcda353d266f605d3bcb2"
          },
          {
            "y": 386,
            "x": 216,
            "u": "https://preview.redd.it/m6ezu85jeh2g1.jpg?width=216&crop=smart&auto=webp&s=65f0202b797d003a7f83d239eb9b3b18cc095dbe"
          },
          {
            "y": 572,
            "x": 320,
            "u": "https://preview.redd.it/m6ezu85jeh2g1.jpg?width=320&crop=smart&auto=webp&s=4a549ef2c71e10f30e7dff7efde13f97bbf6e62b"
          }
        ],
        "s": {
          "y": 735,
          "x": 411,
          "u": "https://preview.redd.it/m6ezu85jeh2g1.jpg?width=411&format=pjpg&auto=webp&s=87ac97889e8a195ba9f76fab0e0f627582d9e53e"
        },
        "id": "m6ezu85jeh2g1"
      },
      "xt8v6o3jeh2g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/png",
        "p": [],
        "s": {
          "y": 61,
          "x": 65,
          "u": "https://preview.redd.it/xt8v6o3jeh2g1.png?width=65&format=png&auto=webp&s=5151c60e6d3fb423fa7e34f355030d8f67155091"
        },
        "id": "xt8v6o3jeh2g1"
      },
      "ueehc03jeh2g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 108,
            "x": 108,
            "u": "https://preview.redd.it/ueehc03jeh2g1.jpg?width=108&crop=smart&auto=webp&s=f1c92ba7ca082169f2d6cee3ec0d8607c29b917b"
          },
          {
            "y": 216,
            "x": 216,
            "u": "https://preview.redd.it/ueehc03jeh2g1.jpg?width=216&crop=smart&auto=webp&s=99932fedf688da4980ae73951a3a404106af1939"
          },
          {
            "y": 320,
            "x": 320,
            "u": "https://preview.redd.it/ueehc03jeh2g1.jpg?width=320&crop=smart&auto=webp&s=a3516504a1749f101303a11018c92711c3f75849"
          }
        ],
        "s": {
          "y": 566,
          "x": 566,
          "u": "https://preview.redd.it/ueehc03jeh2g1.jpg?width=566&format=pjpg&auto=webp&s=f4f8a63a112a9262976b5961419fa875ae549310"
        },
        "id": "ueehc03jeh2g1"
      }
    },
    "gallery_data": {
      "items": [
        {
          "caption": "",
          "media_id": "ueehc03jeh2g1",
          "id": 798822409
        },
        {
          "caption": "",
          "media_id": "m6ezu85jeh2g1",
          "id": 798822410
        },
        {
          "caption": "",
          "media_id": "xt8v6o3jeh2g1",
          "id": 798822411
        }
      ]
    }
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1ozo6h1",
    "title": "BATTLEFIELD 6 GAME UPDATE 1.1.2.0",
    "body": "This update delivers a broad set of improvements to soldier responsiveness, aim consistency, animation fidelity, and overall stability across Battlefield 6. We’ve also introduced a new limited-time mode, refined Aim Assist behaviour, and resolved a large number of weapon, gadget, and vehicle issues based on community feedback. The update will be available tomorrow, November 18th, at 09:00 UTC.\n\nhttps://preview.redd.it/mdng7hkl1v1g1.jpg?width=1920&format=pjpg&auto=webp&s=2b9a31f077e1fc8dd3eb6db39f1e0d025bd4b793\n\n**New Content: California Resistance**\n\n* New Map: Eastwood. A map with the Southern California theme.\n   * Variations of this map will be available for all official modes.\n   * Conquest mode on this map will include tanks, helicopters, and the Golf Cart.\n* New Time-Limited Mode: Sabotage. A themed event mode focused on demolition and counterplay.\n* New Weapons: DB-12 Shotgun and M357 Trait Sidearm. \n* Gauntlet mode to include a new mission type: Rodeo. This mission provides multiple vehicles for players to fight over and battle with each other with. Players earn bonus points for defeating enemies while in a vehicle. \n* Portal updates: \n   * Sandbox map. This option will let Portal experience builders start with a more level playing field to bring their imagination to life. \n   * The Golf Cart vehicle is available for use in building experiences. \n* Battle Pass: The California Resistance bonus path becomes available for a limited time. \n* New underbarrel attachment: Slim Handstop, unlocked via Challenge.\n* New feature coming later in the update: Battle Pickups. These powerful weapons will be available in specific experiences and Portal with limited ammunition but pack enough firepower to help turn the tide of battle in your favor. \n\n**Major Updates for** [**1.1.2.0**](http://1.1.2.0)\n\n* Aim Assist has been reset to its Open Beta tuning, restoring consistent infantry targeting behaviour across all input types.\n* Improved input latency and stick response for controllers, providing smoother aiming and more responsive soldier movement.\n* Weapon accuracy and dispersion tuning: fixed unintended weapon dispersion increase rates and improved non-Recon sniper rifle accuracy while globally reducing dispersion across all weapon types.\n* Challenge and progression clarity improvements make requirements easier to understand and track.\n* Major polish pass to deployable gadgets, including the LWCMS Portable Mortar, LTLM II Portable Laser Designator, and Supply Crate systems.\n* Fort Lyndon added to Portal, expanding available segments for community-created experiences.\n\n**AREAS OF IMPROVEMENT**\n\n**Aim Assist**\n\nAs we got closer to launch, we revisited aim assist tuning based on internal testing and the full range of maps and combat distances coming with release. Our goal was to make aim assist feel more effective beyond mid-range fights which was one of our focuses within Battlefield Labs and Open Beta.\n\nAt launch, we increased slowdown at longer ranges, but once the game went live, we saw that this made high-zoom aiming feel less smooth and harder to control.\n\nAfter reviewing player feedback and gameplay data, we’re reverting aim assist back to the values some of you experienced during Open Beta and Battlefield Labs. This will now serve as the default, whilst still providing you with the ability to alter the aim assist to your preference and playstyle via settings.\n\nThis change keeps aim slowdown consistent across all ranges, helping with muscle memory and providing a steadier, more reliable feel as we move into future seasons.\n\n**CHANGELOG**\n\n**PLAYER:**\n\n* Aim Assist: fully reset to Open Beta tuning, with related options reset to default to ensure consistency.\n* Fixed an issue where Vehicle Stick Acceleration Presets would affect Infantry Aiming Left/Right Acceleration option availability.\n* Fixed an issue where setting Stick Acceleration Presets to “Standard” would set the Aiming Left/Right Acceleration options incorrectly to 50% instead of 70%.\n* Fixed missing Infantry and Vehicle prefixes in captions for Stick Acceleration Presets and Aiming Left/Right Acceleration options.\n* Fixed an issue where stick deadzones would ignore the first 10% of movement if using a PS5 Controller on PC.\n* Fixed an issue where player movement (Left Stick) would not register until beyond 30% of travel past the deadzone.\n* Fixed joystick aiming input behaviour.\n* Added a short sprint “restart” animation when landing from small heights.\n* Added new death animations for sliding and combat-dive states.\n* Fixed a diving loop when entering shallow water.\n* Fixed an issue preventing players from vaulting out of water in certain areas.\n* Fixed an issue preventing takedown initiation against an enemy soldier if the enemy soldier already initiated a takedown against a friendly player.\n* Fixed an issue where a dragged player could face the wrong direction if turning quickly.\n* Fixed an issue where holding a grenade while jumping, sliding, or diving froze the first-person pose.\n* Fixed an issue where switching weapons while drag-reviving would break the reviver’s first-person view.\n* Fixed an issue where the Assault Class extra grenade ability would not grant two grenades on spawn.\n* Fixed an issue where weapons could become invisible when crouching before vaulting.\n* Fixed bouncing behaviour when landing on object edges.\n* Fixed broken ragdolls when killed on ladders, while jumping, near ledges, or in vehicle seats.\n* Fixed camera clipping when dropping from height while prone.\n* Fixed clipping when initiating a drag & revive.\n* Fixed first-person camera clipping through objects when dying nearby.\n* Fixed the issue where the Rush signature trait 'Mission Focused' applied its icon and speed boost to all teammates.\n* Fixed incorrect prone aiming angles on slopes.\n* Fixed misaligned victim position during takedowns when using high FOV settings.\n* Fixed mismatched rotation between first-person and third-person soldier aim directions.\n* Fixed misplaced weapon shadows while vaulting or swimming.\n* Fixed missing pickup prompts while prone.\n* Fixed missing water splash effects while swimming.\n* Fixed stuck third-person soldier animations when entering player view.\n* Fixed teleporting or invisibility when entering vehicles during a vault.\n* Fixed third-person facing inconsistencies when soldiers were mounted.\n* Improved combat-dive animations in first and third person.\n* Improved LTLM II sprint animation in first person.\n* Improved vault detection in cluttered environments.\n* Increased double-tap window for Danger Ping from 0.2 s to 0.333 s.\n* Updated first-person animation cadence for moving up and down stairs.\n* Fixed an issue where hit registration would fail when engaging into gunfights after exiting vehicles.\n\n**VEHICLES:**\n\n* Fixed camera reset when entering an GDF-009 AA Stationary Gun after another user.\n* Fixed clipping gunner weapons in IFV seats.\n* Fixed faint metallic impact sound from M1A2 SEPv3 Main Battle Tank turret wreckage.\n* Fixed several cases where IFV's MR Missile could do more damage than intended to MBT, IFV and AA vehicles\n* Fixed inconsistent projectile video effects on the Abrams main gun.\n* Fixed instant 180-degree turn after exiting a vehicle.\n* Fixed missing scoring for Vehicle Supply when teammates received ammo.\n* Fixed oversized hitbox on UH-79 Helicopter.\n* Fixed passenger and gunner placement issues in the UH-79 Helicopter.\n* Fixed re-entry issues when mounting flipped Quad Bikes.\n* Fixed unintended aim-assist from Attack Helicopters gunner missiles.\n* Fixed unresponsive joystick free-camera controls in transport vehicles.\n\n**WEAPONS:**\n\n* Dispersion tuning pass: dispersion has been globally reduced slightly to reduce its impact on the experience\n* Fixed multiple instances of Canted Reflex and Canted Iron Sight optics clipping with higher-magnification scopes\n* Fixed several issues with underbarrel attachment alignment\n* Fixed minor misplacements or clipping on sights and barrels\n* Fixed missing or incorrect magazine icons, naming, and mesh assignments.\n* Fixed the issue where the SV-98 displayed lower damage stats when equipping the 5 MW Red attachment.\n* Fixed the issue where slug ammunition despawned too quickly after being fired from shotguns.\n* Fixed the issue where the SU-230 LPVO 4x variable scope lacked a smooth transition and audible zoom toggle when aiming down sights.\n* Fixed the issue where two Green Lasers for the DRS-IAR shared identical Hipfire stat boosts.\n* Fixed the issue where impact sparks failed to meet photosensitivity compliance standards.\n* Fixed an issue in third-person where the Mini Scout could clip with the player’s head while aiming.\n* Fixed animation and posture issues affecting the PSR and other rifles when moving or looking at extreme angles.\n* Increased weight of long-range performance in balance for automatic weapons; benefiting PW7A2 and KV9, with minor adjustments elsewhere.\n* Reduced recoil and variation for LMR27, M39, and SVDM for improved long-range reliability.\n\n**GADGETS:**\n\n* Allowed friendly soldiers to damage and detonate certain friendly gadgets.\n* Fixed an issue where Class Ability would sometimes not activate although the UI shows it as available.\n* Fixed auto-deployment of Motion Sensor after recon kit swap.\n* Fixed broken M320A1 Grenade Launcher ground model.\n* Fixed C-4 pickup edge-of-screen interaction.\n* Fixed clipping of the UAV remote when activating it while using certain weapons like rifles.\n* Fixed clipping when holding the CSS Bundle.\n* Fixed CSS Bundle line-of-sight requirements causing unwanted blocking.\n* Fixed Deployable Cover persistence after vehicle destruction.\n* Fixed disappearing “pip” indicator during CSS Bundle supply.\n* Fixed duplicate deploy-audio playback on M4A1 SLAM and C-4.\n* Fixed failed projectile attachment for X95 BRE Breaching Projectile Launcher.\n* Fixed inconsistent hit registration for the Defibrillator after range adjustment.\n* Fixed interaction logic for the Supply Pouch and Assault Ladder.\n* Fixed LTLM II Tripod soldier collision.\n* Fixed M15 AV Mine premature detonation on aircraft wrecks.\n* Fixed M15 AV Mine proximity placement exploit.\n* Fixed missing pickup prompt for thrown C-4 satchels.\n* Fixed MP-APS smoke-propagation failure between friendlies.\n* Fixed multiple haptic and feedback issues on gadgets, including the LWCMS Portable Mortar and the CSB IV Bot Pressure Mine.\n* Fixed placement preview interference from the GPDIS.\n* Fixed XFGM-6D Recon Drone physics allowing vehicle pushing.\n\n**MAPS & MODES:**\n\n* Added Sabotage as a new time-limited event mode.\n* Added the new map “Eastwood”.\n* Fixed black-screen spawn issue with Deploy Beacon in TDM, SDM, Domination, and KOTH.\n* Fixed incomplete or incorrect round-outcome data when joining mid-match.\n* Fixed matchmaking logic to prevent late-stage match joins.\n* Fixed multiple destruction-reset issues after side swap in Strikepoint and Sabotage.\n* Fixed post-insertion movement lock at round start.\n* Fixed unintended AFK kicks while spectating in Strikepoint.\n* Reduced opacity of excessive environmental smoke across multiple maps.\n\n**UI & HUD:**\n\n* Added a message when attempting to change stance without sufficient space.\n* Downed players now appear in the kill log in modes using the crawling downed state (e.g. Strikepoint, REDSEC).\n* Extended top UI on Strikepoint to show detailed alive/downed/dead player counts.\n* Fixed incorrect Assault Training Path icons.\n* Fixed incorrect colour usage on squad-mate health bars.\n* Fixed missing tooltips and UI prompts across tutorials and mission briefings in Single Player.\n* Fixed missing XP Tracker icon at level 3 when using Field Upgrades.\n* Kill-confirmation indicator now displays if a victim bleeds out after being damaged by the player in modes using the crawling downed state (e.g. Strikepoint, REDSEC).\n* Minor UI polish and alignment updates to various game modes.\n* Non-squad friendlies now display a “Thank you!” subtitle after being revived.\n\n**SETTINGS:**\n\n* Added a new option allowing players to sprint automatically when pushing the stick fully forward.\n* Added new keybinding that allows the player to instantly swap to the knife instead of having to hold the button. This keybinding will not allow to perform takedowns contextually but will still allow takedowns to be performed once the melee weapon is equipped.\n\n**SINGLE PLAYER:**\n\n* Addressed multiple occurrences of excessive bright flashes and unintended visual effects.\n* Fixed an issue where AI squadmates would not respond to revive orders and other commands, improving squad functionality and responsiveness.\n* Fixed loss of grenade functionality and shadow-rendering errors in underground areas during the “Moving Mountains” mission.\n* Fixed multiple instances where sound effects or Voice Over would fail to play correctly during gameplay and cinematic moments.\n* Fixed subtitle and audio-video synchronisation issues during gameplay and cinematic sequences.\n* Fixed various instances of corrupted shadows and LOD behaviour when using lower graphics settings.\n* Resolved object clipping and teleporting issues during car-chase sequences in the “Moving Mountains” mission.\n* Resolved several cases of stuttering and desync when using certain graphics presets on NVIDIA and AMD hardware.\n* Resolved several issues that could result in infinite loading screens during mission transitions and save or load operations.\n* Resolved shader stutters in the prologue mission “Always Faithfull”.\n* Fixed issues with party invites not working during campaign loading screens.\n\n**AUDIO:**\n\n* Added new sound effects for Double Ping; refined single and danger ping sound hierarchy.\n* Added new soldier movement and gunfire sound effects, and fixed multiple foley issues.\n* Added turret movement audio for Marauder RWS weapons.\n* Corrected door sound assignments.\n* Corrected swimming, obstruction, and platform footstep audio.\n* Fixed character voice over not updating when changing soldier mid-match.\n* Fixed looped ambient sounds (e.g. food truck) and incorrect debris impacts.\n* Fixed missing first person voice over gasp when revived.\n* Fixed missing third person voice over for explosive deployments.\n* Fixed missing LP voice over zoom audio.\n* Fixed missing ping audio while spectating.\n* Fixed missing reload sound effects when a weapon had 1 bullet remaining.\n* Fixed missing voice over for supply actions and revive requests.\n* Fixed multiple Commander voice over issues.\n* Fixed Music-in-Menus setting not muting music.\n* Fixed seat-change and turret-reload audio on Marauder RWS guns.\n* Fixed underwater breathing voice over and inconsistent swimming audio.\n* Polished Front-End and Loading music transitions between matches.\n* Synced Battle Pass sounds effects to animations.\n* Tweaked light-fixture audio setup.\n* Updated hostile-voice over logic and adjusted reload voice over mix.\n* Updated music urgency system for Portal.\n\n**PORTAL:**\n\n* Added new scripting functions for music control: mod.LoadMusic(), mod.UnloadMusic(), mod.PlayMusic(), mod.SetMusicParam().\n* Fixed RayCast() in ModBuilder to properly detect terrain and environment objects.\n\n**HARDWARE:**\n\n* Fixed an issue where framerate would be be capped to 300FPS with Nvidia cards\n\n**REDSEC**\n\n**VEHICLES:**\n\n* Fixed the issue where the Golf Cart could set off the PTKM-1R gadget in Gauntlet.\n* Fixed persistent gunner MG model after Rhib Boat destruction.\n\n**UI & HUD:**\n\n* Added level display information to the Training Path section within the Class Details screen.\n* Fixed an issue where soldiers and UI elements could be missing in pre-game lobbies after matchmaking.\n* Fixed an issue where the M417 A2 would not appear in kill cards or the kill feed.\n\n**AUDIO:**\n\n* Fixed an issue where the squadmate death sound effect could trigger for non-teammates.\n\n*This announcement may change as we listen to community feedback and continue developing and evolving our Live Service & Content. We will always strive to keep our community as informed as possible.*",
    "author": "battlefield",
    "score": 1685,
    "upvote_ratio": 0.94,
    "num_comments": 1440,
    "subreddit": "Battlefield",
    "created_utc": "2025-11-17T18:31:21.000Z",
    "url": "https://www.reddit.com/r/Battlefield/comments/1ozo6h1/battlefield_6_game_update_1120/",
    "flair": "News",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.Battlefield",
    "thumbnail": "https://b.thumbs.redditmedia.com/NX-pe20QAlr-uBfuL16WafrI76pE_f_atvSXiYdMXZg.jpg",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": {
      "mdng7hkl1v1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 60,
            "x": 108,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=108&crop=smart&auto=webp&s=28afd1f055c8687d3642fffda74f00043643cb13"
          },
          {
            "y": 121,
            "x": 216,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=216&crop=smart&auto=webp&s=517f58978150dfa3ff594404e3277fc91acd0aa7"
          },
          {
            "y": 180,
            "x": 320,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=320&crop=smart&auto=webp&s=5890864bb1fc819a43fe0303e1a1e6bf189d2b55"
          },
          {
            "y": 360,
            "x": 640,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=640&crop=smart&auto=webp&s=3b0aa721a96ec9ed0eaf1e4e8dd85f464ea6b405"
          },
          {
            "y": 540,
            "x": 960,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=960&crop=smart&auto=webp&s=491fac267faa661c671b711cd9854ce36d614068"
          },
          {
            "y": 607,
            "x": 1080,
            "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=1080&crop=smart&auto=webp&s=f033c66f01e9968d9505476b7a1a99cb235f75d0"
          }
        ],
        "s": {
          "y": 1080,
          "x": 1920,
          "u": "https://preview.redd.it/mdng7hkl1v1g1.jpg?width=1920&format=pjpg&auto=webp&s=2b9a31f077e1fc8dd3eb6db39f1e0d025bd4b793"
        },
        "id": "mdng7hkl1v1g1"
      }
    },
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1ozgnxt",
    "title": "Tiefling's Revenge",
    "body": "The air in the Throne Room was thick with the scent of old fear and cheap wine. King Theron, barely twenty-five, was less a ruler and more a depraved child with a kingdom to break. His favorite sport was the grand, horrific spectacle of acquisition: he would ride out, choose a lovely wife from any village, murder her husband on the spot, and drag the woman and her terrified children back to the castle. The women became chattel for his fleeting pleasure; the children, his slaves.\n\nOne day, his guards returned with a woman named Lyra. Theron was immediately captivated by her exotic beauty: the high cheekbones and her subtle ocean blue skin color, a hidden lineage from the ancient days of the Empire of Bael Turath. Her daughter, a small, quiet girl, became one of the kitchen slaves.\n\nWhat the king didn't know was that the woman and her child were direct descendants of a desperate pact, a Tiefling family. Their traits were a devilish whisper of their bloodline, waiting for a catalyst.\n\nThe catalyst came on a cruel autumn evening. Theron, bored and tired of the woman’s misbehavior, killed her on the spot while her daughter watched. As Lyra was stabbed, her last scream awakened something ancient in her daughter. Not the power of a devil, but the inherited, cold will of a thousand generations of power-hungry nobles who made the Nine Hells their business partners. That night, with a silent, terrifying clarity, the child slipped past the guards with silent purpose. She was free.\n\nYears passed. The little girl became a woman; her horns were pronounced, and her skin was the deep crimson of an ancestral bargain. She was known now as Vesper. The vengeance she carried for her mother and the silent memory of the other stolen children became a dark, burning sun that consumed all that was good in her soul. She learned the arcane arts, twisting them into weapons of pure destruction, mirroring the ruthless ambition of her Turathi ancestors. The good woman she might have been perished, replaced by the chilling, pragmatic pursuit of ultimate, unquestionable power.\n\nVesper's path led her back, inevitably, to the jagged spires of Theron's castle.\n\nShe did not need to storm the gates; she knew what the king desired. She entered in the guise of a lady of the night, one of mesmerizing, exotic beauty, using her demonic lineage as a temptation tool. Her magnificent looks and alluring figure were weapons more subtle and deadly than any blade. She used them with the cold, inherited calculation of her ancestors, those power-obsessed nobles of Bael Turath.\n\nShe found King Theron exactly where she knew he would be: not on his throne, but captivated by his own avarice. She allowed him to pursue her, playing the part of the most prized conquest he had ever sought. The illusion was flawless; the seduction, a masterclass in calculated revenge.\n\nFinally, they were alone in the lavish, torch-lit bedroom. The King, unguarded and blinded by desire, dismissed his retinue. The moment the heavy oak doors clicked shut, Vesper's eyes burned with the cold fire of a thousand collected grudges.\n\nTheron gasped, finally seeing the demon he had summoned. Before he could scream, Vesper was on him, moving with the predatory silence of a devil called to collect a debt. In her hand, she held the wicked dragon dagger, a symbol of her destructive power.\n\nShe drove the blade deep into his stomach. But one thrust was not enough for the years of pain she had carried. Vesper twisted the dagger *one, two, three…* ten times, a savage turn for every year of stolen innocence and every year she had lost with her mother.\"Do you remember my mother?\" Vesper's voice was a low rasp, corrupted by years of hate. \"You ended her life for amusement. Today, I end yours for vengeance.\n\n\"Do you remember my mother?\" Vesper's voice was a low rasp, corrupted by years of hate. \"You ended her life for amusement. Today, I end yours for vengeance.\n\nCreated using [AI Game Master](http://aigamemaster.app)",
    "author": "Rich-Witness-6421",
    "score": 1588,
    "upvote_ratio": 0.98,
    "num_comments": 20,
    "subreddit": "dndai",
    "created_utc": "2025-11-17T13:45:19.000Z",
    "url": "https://www.reddit.com/r/dndai/comments/1ozgnxt/tieflings_revenge/",
    "flair": "AI Game Master",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "old.reddit.com",
    "thumbnail": "https://b.thumbs.redditmedia.com/H5EnegINfZxt758WU528jl-gPY-SzXxin0vGp7GKRww.jpg",
    "url_overridden_by_dest": "https://www.reddit.com/gallery/1ozgnxt",
    "media": null,
    "media_metadata": {
      "lmq1e4jymt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/lmq1e4jymt1g1.jpg?width=108&crop=smart&auto=webp&s=c6ca6f29ff1fe683de570b56e398da85590bf0fa"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/lmq1e4jymt1g1.jpg?width=216&crop=smart&auto=webp&s=43a263b67a867c906c282f3763531e22713977cb"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/lmq1e4jymt1g1.jpg?width=320&crop=smart&auto=webp&s=b2990a89ef13491d1fd1aff03abeb00672143842"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/lmq1e4jymt1g1.jpg?width=640&crop=smart&auto=webp&s=33c47ada6b7d780cc6af1d5500983c89a61aa701"
          }
        ],
        "s": {
          "y": 1024,
          "x": 683,
          "u": "https://preview.redd.it/lmq1e4jymt1g1.jpg?width=683&format=pjpg&auto=webp&s=5ea5b369b2e53fbc2cc161130041b3a4f13ac762"
        },
        "id": "lmq1e4jymt1g1"
      },
      "ga48g5xzmt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/png",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=108&crop=smart&auto=webp&s=5dcf8513dc5b7e2095767a876f47124030c3f80f"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=216&crop=smart&auto=webp&s=7cd39831ce5491bdd9cb1ca14dd750f3e72d7b98"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=320&crop=smart&auto=webp&s=f5f6595531e07d54016db01750f04b7c52cc5a6b"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=640&crop=smart&auto=webp&s=9d060345a8cadefb6a1576e167351c5680be6817"
          },
          {
            "y": 1439,
            "x": 960,
            "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=960&crop=smart&auto=webp&s=6afdc496df96f97f41a463b123fa7a85a5ca05e5"
          }
        ],
        "s": {
          "y": 1556,
          "x": 1038,
          "u": "https://preview.redd.it/ga48g5xzmt1g1.png?width=1038&format=png&auto=webp&s=7ca5871784c1ebc910c5df7e2b9f230f1adfefba"
        },
        "id": "ga48g5xzmt1g1"
      },
      "b9v3sb0zmt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/b9v3sb0zmt1g1.jpg?width=108&crop=smart&auto=webp&s=9cde27d9a23f9dac3d55e2d292ae4534e4735fe8"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/b9v3sb0zmt1g1.jpg?width=216&crop=smart&auto=webp&s=730d5610b37c7e152f3f3e21931e468346b945dc"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/b9v3sb0zmt1g1.jpg?width=320&crop=smart&auto=webp&s=d772574c0163854f00571991ae4ca4a3252c865f"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/b9v3sb0zmt1g1.jpg?width=640&crop=smart&auto=webp&s=311f4e976f6a85c17f7982a8ce118949ce3e0c34"
          }
        ],
        "s": {
          "y": 1024,
          "x": 683,
          "u": "https://preview.redd.it/b9v3sb0zmt1g1.jpg?width=683&format=pjpg&auto=webp&s=d9e55e1dae288b25fed72e926b0000a6a5e3c4ee"
        },
        "id": "b9v3sb0zmt1g1"
      },
      "anv62zcymt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/anv62zcymt1g1.jpg?width=108&crop=smart&auto=webp&s=b5e458892f6c38a7a2804dfe3a4ee84fb5894d99"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/anv62zcymt1g1.jpg?width=216&crop=smart&auto=webp&s=b5f1d68eee9bb8e196553ad034811c0a44f13686"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/anv62zcymt1g1.jpg?width=320&crop=smart&auto=webp&s=a3d1ca9b1a852b4d61ab67e71b4300869d514a63"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/anv62zcymt1g1.jpg?width=640&crop=smart&auto=webp&s=7a897799a3aacb69e9ec5f33c7a99562757de3cb"
          }
        ],
        "s": {
          "y": 1024,
          "x": 683,
          "u": "https://preview.redd.it/anv62zcymt1g1.jpg?width=683&format=pjpg&auto=webp&s=8cfb2a867d0c3191cf09cd3614628ceae7670f2e"
        },
        "id": "anv62zcymt1g1"
      },
      "fp0y6tqymt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/fp0y6tqymt1g1.jpg?width=108&crop=smart&auto=webp&s=1a31a9f78cee3fe3424adaed3dd46a855b1260bd"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/fp0y6tqymt1g1.jpg?width=216&crop=smart&auto=webp&s=cefe273cf9db1db7a9197805d835c378ff3c757e"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/fp0y6tqymt1g1.jpg?width=320&crop=smart&auto=webp&s=8006a62391951c1c043687c12c42f566d84341f6"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/fp0y6tqymt1g1.jpg?width=640&crop=smart&auto=webp&s=9da5be769b5dc1221c23a41461f82186b63ec5cd"
          }
        ],
        "s": {
          "y": 1024,
          "x": 683,
          "u": "https://preview.redd.it/fp0y6tqymt1g1.jpg?width=683&format=pjpg&auto=webp&s=19ec0d7005c3231efdb0d2ec459d181b55437d65"
        },
        "id": "fp0y6tqymt1g1"
      },
      "rfwiku5ymt1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 161,
            "x": 108,
            "u": "https://preview.redd.it/rfwiku5ymt1g1.jpg?width=108&crop=smart&auto=webp&s=a5559f938a3b2e9f8d2f7e9ad0b70261fa4120cc"
          },
          {
            "y": 323,
            "x": 216,
            "u": "https://preview.redd.it/rfwiku5ymt1g1.jpg?width=216&crop=smart&auto=webp&s=d6cc0050d029765e357a0511c346ddd9edd1a55e"
          },
          {
            "y": 479,
            "x": 320,
            "u": "https://preview.redd.it/rfwiku5ymt1g1.jpg?width=320&crop=smart&auto=webp&s=d1a919a1c7ac51d0fb3281cf19c0d52b41fa3001"
          },
          {
            "y": 959,
            "x": 640,
            "u": "https://preview.redd.it/rfwiku5ymt1g1.jpg?width=640&crop=smart&auto=webp&s=d62adb796b4d0951281a8e45c1fa3a886e010ed4"
          }
        ],
        "s": {
          "y": 1024,
          "x": 683,
          "u": "https://preview.redd.it/rfwiku5ymt1g1.jpg?width=683&format=pjpg&auto=webp&s=6cbf9f2f14b17f40d20208e5bf2fe732813ad7c9"
        },
        "id": "rfwiku5ymt1g1"
      }
    },
    "gallery_data": {
      "items": [
        {
          "media_id": "fp0y6tqymt1g1",
          "id": 796371441
        },
        {
          "media_id": "rfwiku5ymt1g1",
          "id": 796371442
        },
        {
          "media_id": "lmq1e4jymt1g1",
          "id": 796371443
        },
        {
          "media_id": "anv62zcymt1g1",
          "id": 796371444
        },
        {
          "media_id": "b9v3sb0zmt1g1",
          "id": 796371445
        },
        {
          "media_id": "ga48g5xzmt1g1",
          "id": 796371446
        }
      ]
    }
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1ozo6jj",
    "title": "BATTLEFIELD 6 GAME UPDATE 1.1.2.0",
    "body": "This update delivers a broad set of improvements to soldier responsiveness, aim consistency, animation fidelity, and overall stability across Battlefield 6. We’ve also introduced a new limited-time mode, refined Aim Assist behaviour, and resolved a large number of weapon, gadget, and vehicle issues based on community feedback. The update will be available tomorrow, November 18th, at 09:00 UTC.\n\nhttps://preview.redd.it/ya0b97lm1v1g1.jpg?width=1920&format=pjpg&auto=webp&s=e40fe9759521711ebd2e8a5c836ebf4814ee2aae\n\n**New Content: California Resistance**\n\n* New Map: Eastwood. A map with the Southern California theme.\n   * Variations of this map will be available for all official modes.\n   * Conquest mode on this map will include tanks, helicopters, and the Golf Cart.\n* New Time-Limited Mode: Sabotage. A themed event mode focused on demolition and counterplay.\n* New Weapons: DB-12 Shotgun and M357 Trait Sidearm. \n* Gauntlet mode to include a new mission type: Rodeo. This mission provides multiple vehicles for players to fight over and battle with each other with. Players earn bonus points for defeating enemies while in a vehicle. \n* Portal updates: \n   * Sandbox map. This option will let Portal experience builders start with a more level playing field to bring their imagination to life. \n   * The Golf Cart vehicle is available for use in building experiences. \n* Battle Pass: The California Resistance bonus path becomes available for a limited time. \n* New underbarrel attachment: Slim Handstop, unlocked via Challenge.\n* New feature coming later in the update: Battle Pickups. These powerful weapons will be available in specific experiences and Portal with limited ammunition but pack enough firepower to help turn the tide of battle in your favor. \n\n**Major Updates for** [**1.1.2.0**](http://1.1.2.0)\n\n* Aim Assist has been reset to its Open Beta tuning, restoring consistent infantry targeting behaviour across all input types.\n* Improved input latency and stick response for controllers, providing smoother aiming and more responsive soldier movement.\n* Weapon accuracy and dispersion tuning: fixed unintended weapon dispersion increase rates and improved non-Recon sniper rifle accuracy while globally reducing dispersion across all weapon types.\n* Challenge and progression clarity improvements make requirements easier to understand and track.\n* Major polish pass to deployable gadgets, including the LWCMS Portable Mortar, LTLM II Portable Laser Designator, and Supply Crate systems.\n* Fort Lyndon added to Portal, expanding available segments for community-created experiences.\n\n**AREAS OF IMPROVEMENT**\n\n**Aim Assist**\n\nAs we got closer to launch, we revisited aim assist tuning based on internal testing and the full range of maps and combat distances coming with release. Our goal was to make aim assist feel more effective beyond mid-range fights which was one of our focuses within Battlefield Labs and Open Beta.\n\nAt launch, we increased slowdown at longer ranges, but once the game went live, we saw that this made high-zoom aiming feel less smooth and harder to control.\n\nAfter reviewing player feedback and gameplay data, we’re reverting aim assist back to the values some of you experienced during Open Beta and Battlefield Labs. This will now serve as the default, whilst still providing you with the ability to alter the aim assist to your preference and playstyle via settings.\n\nThis change keeps aim slowdown consistent across all ranges, helping with muscle memory and providing a steadier, more reliable feel as we move into future seasons.\n\n**CHANGELOG**\n\n**PLAYER:**\n\n* Aim Assist: fully reset to Open Beta tuning, with related options reset to default to ensure consistency.\n* Fixed an issue where Vehicle Stick Acceleration Presets would affect Infantry Aiming Left/Right Acceleration option availability.\n* Fixed an issue where setting Stick Acceleration Presets to “Standard” would set the Aiming Left/Right Acceleration options incorrectly to 50% instead of 70%.\n* Fixed missing Infantry and Vehicle prefixes in captions for Stick Acceleration Presets and Aiming Left/Right Acceleration options.\n* Fixed an issue where stick deadzones would ignore the first 10% of movement if using a PS5 Controller on PC.\n* Fixed an issue where player movement (Left Stick) would not register until beyond 30% of travel past the deadzone.\n* Fixed joystick aiming input behaviour.\n* Added a short sprint “restart” animation when landing from small heights.\n* Added new death animations for sliding and combat-dive states.\n* Fixed a diving loop when entering shallow water.\n* Fixed an issue preventing players from vaulting out of water in certain areas.\n* Fixed an issue preventing takedown initiation against an enemy soldier if the enemy soldier already initiated a takedown against a friendly player.\n* Fixed an issue where a dragged player could face the wrong direction if turning quickly.\n* Fixed an issue where holding a grenade while jumping, sliding, or diving froze the first-person pose.\n* Fixed an issue where switching weapons while drag-reviving would break the reviver’s first-person view.\n* Fixed an issue where the Assault Class extra grenade ability would not grant two grenades on spawn.\n* Fixed an issue where weapons could become invisible when crouching before vaulting.\n* Fixed bouncing behaviour when landing on object edges.\n* Fixed broken ragdolls when killed on ladders, while jumping, near ledges, or in vehicle seats.\n* Fixed camera clipping when dropping from height while prone.\n* Fixed clipping when initiating a drag & revive.\n* Fixed first-person camera clipping through objects when dying nearby.\n* Fixed the issue where the Rush signature trait 'Mission Focused' applied its icon and speed boost to all teammates.\n* Fixed incorrect prone aiming angles on slopes.\n* Fixed misaligned victim position during takedowns when using high FOV settings.\n* Fixed mismatched rotation between first-person and third-person soldier aim directions.\n* Fixed misplaced weapon shadows while vaulting or swimming.\n* Fixed missing pickup prompts while prone.\n* Fixed missing water splash effects while swimming.\n* Fixed stuck third-person soldier animations when entering player view.\n* Fixed teleporting or invisibility when entering vehicles during a vault.\n* Fixed third-person facing inconsistencies when soldiers were mounted.\n* Improved combat-dive animations in first and third person.\n* Improved LTLM II sprint animation in first person.\n* Improved vault detection in cluttered environments.\n* Increased double-tap window for Danger Ping from 0.2 s to 0.333 s.\n* Updated first-person animation cadence for moving up and down stairs.\n* Fixed an issue where hit registration would fail when engaging into gunfights after exiting vehicles.\n\n**VEHICLES:**\n\n* Fixed camera reset when entering an GDF-009 AA Stationary Gun after another user.\n* Fixed clipping gunner weapons in IFV seats.\n* Fixed faint metallic impact sound from M1A2 SEPv3 Main Battle Tank turret wreckage.\n* Fixed several cases where IFV's MR Missile could do more damage than intended to MBT, IFV and AA vehicles\n* Fixed inconsistent projectile video effects on the Abrams main gun.\n* Fixed instant 180-degree turn after exiting a vehicle.\n* Fixed missing scoring for Vehicle Supply when teammates received ammo.\n* Fixed oversized hitbox on UH-79 Helicopter.\n* Fixed passenger and gunner placement issues in the UH-79 Helicopter.\n* Fixed re-entry issues when mounting flipped Quad Bikes.\n* Fixed unintended aim-assist from Attack Helicopters gunner missiles.\n* Fixed unresponsive joystick free-camera controls in transport vehicles.\n\n**WEAPONS:**\n\n* Dispersion tuning pass: dispersion has been globally reduced slightly to reduce its impact on the experience\n* Fixed multiple instances of Canted Reflex and Canted Iron Sight optics clipping with higher-magnification scopes\n* Fixed several issues with underbarrel attachment alignment\n* Fixed minor misplacements or clipping on sights and barrels\n* Fixed missing or incorrect magazine icons, naming, and mesh assignments.\n* Fixed the issue where the SV-98 displayed lower damage stats when equipping the 5 MW Red attachment.\n* Fixed the issue where slug ammunition despawned too quickly after being fired from shotguns.\n* Fixed the issue where the SU-230 LPVO 4x variable scope lacked a smooth transition and audible zoom toggle when aiming down sights.\n* Fixed the issue where two Green Lasers for the DRS-IAR shared identical Hipfire stat boosts.\n* Fixed the issue where impact sparks failed to meet photosensitivity compliance standards.\n* Fixed an issue in third-person where the Mini Scout could clip with the player’s head while aiming.\n* Fixed animation and posture issues affecting the PSR and other rifles when moving or looking at extreme angles.\n* Increased weight of long-range performance in balance for automatic weapons; benefiting PW7A2 and KV9, with minor adjustments elsewhere.\n* Reduced recoil and variation for LMR27, M39, and SVDM for improved long-range reliability.\n\n**GADGETS:**\n\n* Allowed friendly soldiers to damage and detonate certain friendly gadgets.\n* Fixed an issue where Class Ability would sometimes not activate although the UI shows it as available.\n* Fixed auto-deployment of Motion Sensor after recon kit swap.\n* Fixed broken M320A1 Grenade Launcher ground model.\n* Fixed C-4 pickup edge-of-screen interaction.\n* Fixed clipping of the UAV remote when activating it while using certain weapons like rifles.\n* Fixed clipping when holding the CSS Bundle.\n* Fixed CSS Bundle line-of-sight requirements causing unwanted blocking.\n* Fixed Deployable Cover persistence after vehicle destruction.\n* Fixed disappearing “pip” indicator during CSS Bundle supply.\n* Fixed duplicate deploy-audio playback on M4A1 SLAM and C-4.\n* Fixed failed projectile attachment for X95 BRE Breaching Projectile Launcher.\n* Fixed inconsistent hit registration for the Defibrillator after range adjustment.\n* Fixed interaction logic for the Supply Pouch and Assault Ladder.\n* Fixed LTLM II Tripod soldier collision.\n* Fixed M15 AV Mine premature detonation on aircraft wrecks.\n* Fixed M15 AV Mine proximity placement exploit.\n* Fixed missing pickup prompt for thrown C-4 satchels.\n* Fixed MP-APS smoke-propagation failure between friendlies.\n* Fixed multiple haptic and feedback issues on gadgets, including the LWCMS Portable Mortar and the CSB IV Bot Pressure Mine.\n* Fixed placement preview interference from the GPDIS.\n* Fixed XFGM-6D Recon Drone physics allowing vehicle pushing.\n\n**MAPS & MODES:**\n\n* Added Sabotage as a new time-limited event mode.\n* Added the new map “Eastwood”.\n* Fixed black-screen spawn issue with Deploy Beacon in TDM, SDM, Domination, and KOTH.\n* Fixed incomplete or incorrect round-outcome data when joining mid-match.\n* Fixed matchmaking logic to prevent late-stage match joins.\n* Fixed multiple destruction-reset issues after side swap in Strikepoint and Sabotage.\n* Fixed post-insertion movement lock at round start.\n* Fixed unintended AFK kicks while spectating in Strikepoint.\n* Reduced opacity of excessive environmental smoke across multiple maps.\n\n**UI & HUD:**\n\n* Added a message when attempting to change stance without sufficient space.\n* Downed players now appear in the kill log in modes using the crawling downed state (e.g. Strikepoint, REDSEC).\n* Extended top UI on Strikepoint to show detailed alive/downed/dead player counts.\n* Fixed incorrect Assault Training Path icons.\n* Fixed incorrect colour usage on squad-mate health bars.\n* Fixed missing tooltips and UI prompts across tutorials and mission briefings in Single Player.\n* Fixed missing XP Tracker icon at level 3 when using Field Upgrades.\n* Kill-confirmation indicator now displays if a victim bleeds out after being damaged by the player in modes using the crawling downed state (e.g. Strikepoint, REDSEC).\n* Minor UI polish and alignment updates to various game modes.\n* Non-squad friendlies now display a “Thank you!” subtitle after being revived.\n\n**SETTINGS:**\n\n* Added a new option allowing players to sprint automatically when pushing the stick fully forward.\n* Added new keybinding that allows the player to instantly swap to the knife instead of having to hold the button. This keybinding will not allow to perform takedowns contextually but will still allow takedowns to be performed once the melee weapon is equipped.\n\n**SINGLE PLAYER:**\n\n* Addressed multiple occurrences of excessive bright flashes and unintended visual effects.\n* Fixed an issue where AI squadmates would not respond to revive orders and other commands, improving squad functionality and responsiveness.\n* Fixed loss of grenade functionality and shadow-rendering errors in underground areas during the “Moving Mountains” mission.\n* Fixed multiple instances where sound effects or Voice Over would fail to play correctly during gameplay and cinematic moments.\n* Fixed subtitle and audio-video synchronisation issues during gameplay and cinematic sequences.\n* Fixed various instances of corrupted shadows and LOD behaviour when using lower graphics settings.\n* Resolved object clipping and teleporting issues during car-chase sequences in the “Moving Mountains” mission.\n* Resolved several cases of stuttering and desync when using certain graphics presets on NVIDIA and AMD hardware.\n* Resolved several issues that could result in infinite loading screens during mission transitions and save or load operations.\n* Resolved shader stutters in the prologue mission “Always Faithfull”.\n* Fixed issues with party invites not working during campaign loading screens.\n\n**AUDIO:**\n\n* Added new sound effects for Double Ping; refined single and danger ping sound hierarchy.\n* Added new soldier movement and gunfire sound effects, and fixed multiple foley issues.\n* Added turret movement audio for Marauder RWS weapons.\n* Corrected door sound assignments.\n* Corrected swimming, obstruction, and platform footstep audio.\n* Fixed character voice over not updating when changing soldier mid-match.\n* Fixed looped ambient sounds (e.g. food truck) and incorrect debris impacts.\n* Fixed missing first person voice over gasp when revived.\n* Fixed missing third person voice over for explosive deployments.\n* Fixed missing LP voice over zoom audio.\n* Fixed missing ping audio while spectating.\n* Fixed missing reload sound effects when a weapon had 1 bullet remaining.\n* Fixed missing voice over for supply actions and revive requests.\n* Fixed multiple Commander voice over issues.\n* Fixed Music-in-Menus setting not muting music.\n* Fixed seat-change and turret-reload audio on Marauder RWS guns.\n* Fixed underwater breathing voice over and inconsistent swimming audio.\n* Polished Front-End and Loading music transitions between matches.\n* Synced Battle Pass sounds effects to animations.\n* Tweaked light-fixture audio setup.\n* Updated hostile-voice over logic and adjusted reload voice over mix.\n* Updated music urgency system for Portal.\n\n**PORTAL:**\n\n* Added new scripting functions for music control: mod.LoadMusic(), mod.UnloadMusic(), mod.PlayMusic(), mod.SetMusicParam().\n* Fixed RayCast() in ModBuilder to properly detect terrain and environment objects.\n\n**HARDWARE:**\n\n* Fixed an issue where framerate would be be capped to 300FPS with Nvidia cards\n\n**REDSEC**\n\n**VEHICLES:**\n\n* Fixed the issue where the Golf Cart could set off the PTKM-1R gadget in Gauntlet.\n* Fixed persistent gunner MG model after Rhib Boat destruction.\n\n**UI & HUD:**\n\n* Added level display information to the Training Path section within the Class Details screen.\n* Fixed an issue where soldiers and UI elements could be missing in pre-game lobbies after matchmaking.\n* Fixed an issue where the M417 A2 would not appear in kill cards or the kill feed.\n\n**AUDIO:**\n\n* Fixed an issue where the squadmate death sound effect could trigger for non-teammates.\n\n*This announcement may change as we listen to community feedback and continue developing and evolving our Live Service & Content. We will always strive to keep our community as informed as possible.*",
    "author": "battlefield",
    "score": 878,
    "upvote_ratio": 0.97,
    "num_comments": 900,
    "subreddit": "Battlefield6",
    "created_utc": "2025-11-17T18:31:25.000Z",
    "url": "https://www.reddit.com/r/Battlefield6/comments/1ozo6jj/battlefield_6_game_update_1120/",
    "flair": "Battlefield Studios Official",
    "over_18": false,
    "is_self": true,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "self.Battlefield6",
    "thumbnail": "self",
    "url_overridden_by_dest": null,
    "media": null,
    "media_metadata": {
      "ya0b97lm1v1g1": {
        "status": "valid",
        "e": "Image",
        "m": "image/jpg",
        "p": [
          {
            "y": 60,
            "x": 108,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=108&crop=smart&auto=webp&s=572c30c5702c3f93eca5b1044a0caec8a067d509"
          },
          {
            "y": 121,
            "x": 216,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=216&crop=smart&auto=webp&s=1089f16b45b0f672929e50276e95f671a359bafc"
          },
          {
            "y": 180,
            "x": 320,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=320&crop=smart&auto=webp&s=d7367f864dfbd76a5d6ac062bf4759a21cc9bf99"
          },
          {
            "y": 360,
            "x": 640,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=640&crop=smart&auto=webp&s=cc1fc987341a9926da55a93ae5f6bceb4b447c2b"
          },
          {
            "y": 540,
            "x": 960,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=960&crop=smart&auto=webp&s=e4f3abcab8a95f03a8b78b497e3294dbadb99f28"
          },
          {
            "y": 607,
            "x": 1080,
            "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=1080&crop=smart&auto=webp&s=6bf6fbdd1289dedf750b700209474b3d03e98f61"
          }
        ],
        "s": {
          "y": 1080,
          "x": 1920,
          "u": "https://preview.redd.it/ya0b97lm1v1g1.jpg?width=1920&format=pjpg&auto=webp&s=e40fe9759521711ebd2e8a5c836ebf4814ee2aae"
        },
        "id": "ya0b97lm1v1g1"
      }
    },
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p09gh5",
    "title": "As Arc Raiders faces backlash for its AI voices, Dispatch leads call the tech \"a production solution, not a creative one,\" saying it can only offer \"something you've heard before\"",
    "body": "",
    "author": "MaintenanceFar4207",
    "score": 853,
    "upvote_ratio": 0.88,
    "num_comments": 467,
    "subreddit": "PS5",
    "created_utc": "2025-11-18T11:26:18.000Z",
    "url": "https://www.reddit.com/r/PS5/comments/1p09gh5/as_arc_raiders_faces_backlash_for_its_ai_voices/",
    "flair": "Articles & Blogs",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "gamesradar.com",
    "thumbnail": "https://external-preview.redd.it/X-WkWjaIqX-fvXUCy4JmFSnzhM1scLNjgdrcL40tK9c.jpeg?width=140&height=78&auto=webp&s=c76e390a5c27e0d887ad380b2d1de1c0c6ce023e",
    "url_overridden_by_dest": "https://www.gamesradar.com/games/adventure/as-arc-raiders-faces-backlash-for-its-ai-voices-dispatch-leads-call-the-tech-a-production-solution-not-a-creative-one-saying-it-can-only-offer-something-youve-heard-before/",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p2cc86",
    "title": "LIMIT $100/$200 - In for $8,000, Out for $41,400",
    "body": "Fellow r/poker degens, I must tell you that I feel called to write a session report. It's been a while since my last post, but I find that \"life gets in the way\". \n\nRecently I've experienced some extended rungood (along with a couple of disastrous, donk-tastic sessions mixed in there as well). Here, I'll share some highlights of a triumphant session from about a week ago. Bought in for $8,000 and cashed out for $41,400. (Profit of +$31,400.) The whole session lasted a little over 6.5 hours, which means my hourly win-rate was a healthy (and wholly-unsustainable over the long term) $5,100/hr.\n\nI think just about all of this detail to follow is accurate, but the session isn't so fresh in my memory. As Napoleon said, \"What is history, but a fable agreed upon.\" Right?\n\nAm I perfect? No. Am I trying to be a better person? Also no. \n\nHousekeeping notes: \n\n1) This game is LIMIT $100/$200 (it's NOT No-Limit) at Bay101 in San Jose. The blinds are $50/$100/$200. Four-bet cap on each street, so max-pain is $400 per player preflop/flop, and then $800 on both Turn and River. \n\n2) This session report comes during nonstop “Team Game”, in which the table is broken into multiple equal-sized teams (three teams of 3 or four teams of 2). Normal play proceeds but if you or your teammates wins the hand, then your team gets 1 point. First team to 7 points (sometimes we choose to play to 8 points), wins the game. Payouts from the losing team can range from a few hundred to a few thousand $$, depending on the situation. \n\n3) Playing Team Game creates a mind-warping amount of action and throws an element of chaos into the otherwise stoic, mathematically-solved word of Limit Hold'em. (For you smooth-brained homonculi who deride Limit Hold'em as being somewhat \"beneath you\", or who look down your delicately-tapered noses at those of us who play Limit, I have this to say to you: You're adorable.)\n﻿\nSome noteworthy hands from the session that I can share: \n\nOBLIGATORY BAD BEAT: In my second or third orbit after being seated, I pick up black Aces on the button. It's capped at $400 before it gets to me so I slap down four white chips and we go six-handed to the Flop. $2550 in the center.\n\nFlop comes: (8 5 2) rainbow\n\nNothing too scary on that board. One of the true sharks at the table, a consistent big winner who is a crusher, a pro, and gives plenty of action (so we'll call him CAP in this report, which stands for Crusher-Action-Pro) bets right into the field, as he was the original raiser. Then Sid (Super-Impossible-Donkey) -- who incidentally is one of the five worst players to ever sit down at a cash poker table -- immediately raises to $200. Call, call, and I three-bet it. Two people fold, Cap calls the raises and Sid caps it. $4150 in the pot now. \n\nTurn comes: 8 5 2 (J)\n\nCheck-check-checky over to me and I fire $200. Fold, Cap calls and Sid check-raises to $400. Sid splashes the chips around like a madman, so this raise could be seen as meaningless. Dude sprays more wildly than an unmanned fire hose. \n\nSo while this Turn check-raise might (if coming from a normal player) be an indication of a slow-played set or perhaps J-8, I'm thinking it's more likely that Sid raised the flop on the come with overcards (K-J, Q-J or some such) and spiked a Jack. \n\nIt's a trifling matter, because I'm not folding an overpair. You think I'd fold Aces there? Bruh, you'd better tie your shoelaces right now, 'cuz you trippin'. \n\nOn the contrary, I 3-bet, Cap calls and then Sid caps it. The fourth dude who had been hitchhiking with us finally got out of the way, so three of us head to the River with $6550 in the middle. \n\nRiver comes 8 5 2 J (5)\n\nNow with that River card, I'm PRAYING Sid has J-8. Both of them check to me and I obligingly bet. Then CAP raises me! Ai-yaa! Cap might do a bit of exploratory betting/raising on the cheaper streets, as a way to troll for information, but this River check-raise is not a bluff. Never a bluff. My Aces will suffer an undignified death. Not a quick, soldier's death.\n\nSid calls and I do the \"crying call\". Cap flips up 5-4 suited. (For those of you who might say that no one who could be described as a \"Crusher Pro\" would EVER play 5-4 in a game of this size, I'll remind you that - in our Team Game - there are three different Bonus Hands that are worth TWO POINTS to your team: 7-2, 7-4, and 5-4). So everyone plays those hands when Team Game is ON, because the desire to bad-beat someone with a Bonus Hand is rapacious. So when Cap hit second pair on the flop, he felt obliged to stick around and wait for a 5 or a 4 to tumble off the deck by the river, which is precisely what happened. \n\nHe went a LONG way for that third five, and paid dearly for it. To quote Nic Cage from 'The Rock', as he's locked in a cell and talking to Sean Connery: \n\n\"You broke out, let me see if I can get this straight, down the incinerator chute, on the mine car, through the tunnels to the power plant, under the steam engine - that was really cool by the way - and into the cistern through the intake pipe. But how, in the name of Zeus' BUTTHOLE!... did you get out of your cell?! I only ask because in our current situation, well, it could prove to be useful information. *Maybe*!\"\n\nOBLIGATORY COLD DECK: I'm dealt the pointy 8's (8 of Diamonds/8 of Spades) in the Straddle. It's capped ahead of me and I call the $200. Sid is in this hand (obv, almost goes without saying) and he was the first raiser preflop. One of my teammates caps it with TT. This guy is a really good dude, I dig playing poker with him and being his teammate when we're paired up; and I'd reckon he's about a break-even player over the long-term. So we'll call him BELT (for Break Even Long Term). \n\nFlop comes (T 3 3)\n\nNot an ideal flop for my 88, but have you ever noticed that when you miss the Flop, you either look for reasons to call? Or you look for reasons to fold? At this moment, I was immersed in the former camp -- looking for reasons to call. So I convinced myself that no one had a Ten, and it was 33% less likely that anyone had a three. \n\nPlus, who cares if I was up against A-3 or Jack-Ten s00ted (aka \"Asian Aces\")?! I was hunting an 8 on the Turn. And if I missed the Turn, then I'd happily suck an Eight out on the River. \n\nHow was I to know that Belt had me completely boxed in with his Pocket Tens? I was drawing stone-ass dead (save for runner-runner eights). I had no options, and he knew it. \n\n\"You alert the media, I launch the gas. You refuse payment, I launch the gas. You've got forty hours, until noon, day after tomorrow, to arrange transfer of the money. I am aware of your countermeasure. You know, and I know, it doesn't stand a chance. Hummel from Alcatraz, OUT!\"\n\nOf course my Eight came on the Turn, and I got punished badly. What a gross, gratuitous, and unnecessary turn card. \n\nHave I mentioned that when I write my poker memoir, the title of the book will be, \"Drawing Dead and Getting There\"? \n\nSo I'd say the first hour or so of this session started out \"sub-optimally\" for ole' Buford (that's me). \n\nBut then my river of frozen cards started to thaw. I hit some sets, won a couple of flips, and skunked a few suckas in Team Game. My eroded stack started to replenish itself, like it was comprised of self-healing nanobots. \n\nOBLIGATORY GOOD BEAT: I've got Kd6d in the CO and Sid has A6o in MP. My team has 5 points in the Team Game (Belt and Cap are my teammates), and Sid is on a different team and they've got the lead. It's 6 to 5 to 2 at the moment, meaning Sid's team has Game Point. If they win one more hand, they'll take down Team Game. I think Sid has scored like five of his team's six points in this game.\n\nAll of this to say, I don't WANT to call three bets cold with K-6 suited, but I feel COMPELLED to do it. For the team! Cap has already folded, but I know Belt will \"have my six\", as it were (i.e. \"watch my back\"). \n\nSure enough, Belt is in there with me, along with one of the players on the third-place team. \n\nFlop is: (9 6 2)\n\nSid: A-6\nMe: K-6\nBelt: 22\nDonkey from the Third-place team: ???\n\nI have no idea what I'm up against, but it's a scary spot, to be sure, even though I have position on everyone for this hand. Middle pair is unlikely to be leading at this point, and the table is going to put a lot of pressure on me. \n\n\"Look, I'm just a biochemist. Most of the time, I work in a little glass jar and lead a very uneventful life. I drive a Volvo, a beige one. But what I'm dealing with here is one of the most deadly substances the earth has ever known, so what say you cut me some FRIGGIN' SLACK?!\"\n\nIt's capped on the flop, four ways -- which was as certain of an outcome as someone in a white Tesla driving like an A-hole in the freeway lane next to yours. Absolutely guaranteed. $3300 in the pot. \n\nTurn comes: 9 6 2 (K)\n\nThat turn card gives me more comfort than a warm hug from a chubby Aunt at a family reunion. My two pair has to be good here, right? How was I to know that Belt had flopped another set on me, and then I got spectacularly unlucky by improving on the Turn when in actuality it just got me into more trouble?\n\nCapped four ways on the Turn, with Last-Place guy hanging in there desperately, in an attempt to keep his team from losing. $4900 in the middle.\n\nRiver comes: 9 6 2 K (6) \n\nAhh, sweet redemption. Worst-to-first? I'll take it. Not only does that paired board give Belt the smallest full house, but it gives Sid trip Sixes with an Ace kicker! But my full house mo' better!\n\nIn a very democratic display, each one of us got a chance to raise on the River, all being certain that we had the best hand. \n\nIt was a very tense standoff. But our team (me & Belt) had the high ground, and Sid was boxed in below us with zero chance of survival.\n\nGeneral Hummel: “Major Anderson, if you have any concern for the lives of your men, you will order them to safety their weapons and place them on the deck.”\n\nCommander Anderson: “Sir, we know why you're out here. God knows, I agree with you. But like you, I swore to defend this country against all enemies, foreign, sir... and domestic. General, we've spilled the same blood in the same mud. And you know goddamn well I can't give that order.”\n\nGeneral Hummel: “Your unit is covered from an elevated position, Commander. I'm not gonna ask you again. Don't do anything stupid. No one has to die here.”\n\nCommander Anderson: [raising his voice] “You men following the General: you're under oath as United States Marines, have you forgotten that? We all have shipmates we remember, some of them were shit on and pissed on by the Pentagon. But that doesn't give you the right to mutiny!”\n\nGeneral Hummel: “You call it what you want! You're down there, we're up here! You walked into the wrong goddamn room, Commander!”\n\nWhen I tabled my cards and placed them on the deck, Belt and Sid reacted with \"shock and horrah\". Sid's reaction was something like, \"Hey, quick question: are you fukn kidding me?!\" (but imagine it spoken in an Indian accent). \n\nBelt reacted with something like, \"Son, you got too much salsa on your tortilla chip.\" (but in a Farsi accent). Those might not be EXACT recitations of what they said, but the gist is the same -- \"Inconceivable!\" (spoken with Vezzini's lisp from 'Princess Bride'). \n\n\"I'd take pleasure in guttin' you, boy. I'd take pleasure in guttin' you... boy.\" What is wrong with these people, huh, Mason? Don't you think there's a lot of, uh, a lot of anger flowing around this island? Kind of a pubescent volatility? Don't you think? A lotta angst, a lot of \"I'm sixteen, I'm angry at my father\" syndrome? I mean grow up! We're stuck on an island with a bunch of violence-for-pleasure-seeking psychopathic Marines, SHAME! ON! THEM!\"\n\nWith that hand our team (me/Belt/Cap) had Game Point our own damn selves, the score now being: 6/6/2. \n\nOn the VERY next hand I tell you, I peel up the corners of my cards and look down at 9-5 of Clubs. Even in the craziness of Team Game, I typically would snap-muck that hand. But we had Game Point! What if I was getting on a rush?! One of my worst feelings in poker is being on a huge rush that you're NOT playing (i.e. folding several hands in a row that all would have won). \n\nSo when Sid opened for a raise, I capped it without hesitation. I was only mildly surprised when the flop appeared. \n\nFlop comes (9 9 5)\n\nOf course it did! This time, Sid had Aces, which was unfortunate for him (as the old poker aphorism goes, \"Statistically, donkeys get Aces as often as anyone else.\")\n\nWhat's even crazier is that Belt had red Fours and the Turn came a four! \n\nFor the second straight hand, poor Belt made an under-full that got crushed into powder. I'm talking a finely-crushed powder that's smoother than clamshells ground up to make the surface of a bocce ball court. \n\nEven though we won the Team Game, he'd had ENOUGH of me by that point and only begrudgingly accepted my fist bump as a victorious teammate. He muttered something under his breath about it being the most abnormal shit he'd ever seen. \n\nI beg to differ -- in this $100/$200 game, it's utterly routine.\n\n“Stanley Goodspeed (pointing to a dead Marine's foot that is twitching): You've been around a lot of corpses. Is that normal?!\n\nJohn Mason: What, the feet thing?\n\nStanley Goodspeed: Yeah, the feet thing.\n\nJohn Mason: Yeah, it happens.\n\nStanley Goodspeed: Well I'm having a hard time concentrating. Can you do something about it?\n\nJohn Mason: Like what? Kill him again?”\n\n\nA short while later, I racked up my imposing tower of $40k+ and sashayed over to the cage to watch the cash-counting machines whir and spin. \n\nUntil next time, I remain your humble Limit Hold'em narrator and tour guide. \n\nBuford T. Justice, from Bay101. OUT! ",
    "author": "BufordTeeJustice",
    "score": 845,
    "upvote_ratio": 0.97,
    "num_comments": 152,
    "subreddit": "poker",
    "created_utc": "2025-11-20T19:21:22.000Z",
    "url": "https://www.reddit.com/r/poker/comments/1p2cc86/limit_100200_in_for_8000_out_for_41400/",
    "flair": "BBV",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "i.redd.it",
    "thumbnail": "https://b.thumbs.redditmedia.com/OJklvZYG2UTW9fPBfKBZrZ-nBqKPBYXG5TBeixIMlUI.jpg",
    "url_overridden_by_dest": "https://i.redd.it/zy5sd1zxpg2g1.jpeg",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p34i8x",
    "title": "Reviewing TBC Loot Systems",
    "body": "Hey all, happy Friday. In light of the TBC changes (most of which are awesome), many folks are hoping for more clarity concerning The Loot System That Shall Not Be Named.\n\nIts looking like time spent in raids overall will be drastically reduced compared to 2021 with post-nerf changes and Lady Vashj & Kaelthas no longer being a hard gap which resulted in several wipes per night for most guilds as they progged through Tier 5.\n\nWith more time, means more alts. More alts means more raids - many of which will be PUG driven as a ton of guilds (including my own) only have 1-2 main runs and pug most of the alt runs. For those who have the time, alts are a fun way to enjoy the game on a class you generally don't main.\n\nA giant pitfall that we encountered on Nightslayer (US) was that alts were too costly gold-wise to maintain for many folks, myself included. Sure, you don't need to spend 300+ gold per raid prior to Naxx - but tons of folks enjoy flasking and spending gold on high damage consumables like Elixir of the Mongoose which were a staggering 20g+ per for most of the expansion. The costs added up fast, and alts within our horde guild diminished quickly as folks realized they didn't have the time to farm the gold to supply these alts with the obscene consumable prices.\n\nI realize that the majority of this reddit has a hardline stance against GDKP. This is fair, as in the past it was strongly believed that GDKP incentivized and increased gold buying. Having attended a successful SR pug raid for all of Classic, I strongly believe now that **\\*\\* enabling GDKP would heavily reduce gold buying for all Anniversary servers\\*\\***. Every week in the SR run and across Anniversary discords, people lament openly about needing to buy gold just to raid. Its seemingly become widespread and disturbingly does not have the same shame once attached to it. Myself nor my guildies would ever buy gold, but we encounter new faces and voices each week who talk very openly about it. This is a massive problem.\n\nOn top of that, the soft reserve / hard reserve system has become entirely unhinged. We are proud to be a part of one of the only 15/15 Naxx pug runs that does not hard reserve loot. That said, there are TONS of SR/HR runs that will openly sell loot GDKP-style or even for hard cash. The (AI?) GM responses we've seen when reporting this behavior states that \"Individual players are allowed to sell loot for gold, no matter how immoral this may seem.\" This is a disgusting practice where raid leads are **\\*legally\\*** allowed to pocket the gold from items they sell, instead of sharing it amongst the 40 players who \\*made the raid possible.\\* I have seen confirmed screenshots and heard stories of raid leaders pocketing $900 cash for single items, while hoarding in nearly 100k gold for other single items. *Why is this as a practice allowed when sharing it amongst the people is a far more moral system?*\n\nI have experienced both GDKP and this SR/HR system at length. I strongly believe GDKP is the superior system in every sense - it rewards regular attendance and regulates itself perfectly. Soft Reserve on the other hand is sheer luck, a regular attendee can lose 10 items or win 10 items in a row. This does not encourage safe and fair loot distribution.\n\nPlease share thoughts below - hate to bring up such an incendiary topic but having more communication from Blizzard regarding these exploited systems and the possible restoration of GDKP would be great.",
    "author": "Enthozz",
    "score": 520,
    "upvote_ratio": 0.73,
    "num_comments": 731,
    "subreddit": "classicwow",
    "created_utc": "2025-11-21T17:20:01.000Z",
    "url": "https://www.reddit.com/r/classicwow/comments/1p34i8x/reviewing_tbc_loot_systems/",
    "flair": "Classic 20th Anniversary Realms",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "i.redd.it",
    "thumbnail": "https://b.thumbs.redditmedia.com/NLFKqUbYq419yI65sdhadxRIjgIkYuuTlLd3Y1FMA0U.jpg",
    "url_overridden_by_dest": "https://i.redd.it/72tnrqt59n2g1.jpeg",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  },
  {
    "kind": "post",
    "query": "voice ai",
    "id": "1p2sd3j",
    "title": "As much as i wanna find an excuse there isn't.",
    "body": "This isn't something to be silent about, this isn't something to ignore\n\nIf they will continue with this the quality of the game will worsen by a significant amount i mean alone the Times where they have used ai you could tell that they did. That alone says alot about the quality of the game, but with the amount of ai added people are bound to lose their jobs. \n\nAi can be usefull but not for this, Generative ai isn't quality enhancing it takes away soul. Even for a game centerd for kids who would want kids to grow up with Ai generated slop. \n\nDon't be silent, don't ignore this. Yes Reddit is a Loud minority and i couldn't care enough to open this app once a Bluemoon i will still post this here. If you're gonna go \"oh well we can't do anything anyway\" then yes nothing will happen. Voice ur disinterrest FOR the interrest of the games future, Speak up. Make yourself heard.\n\nI don't care if this post will get downvoted into oblivion i'm not on this app enough to care. But i'm not gonna be silent",
    "author": "Working-Monk7149",
    "score": 514,
    "upvote_ratio": 0.92,
    "num_comments": 110,
    "subreddit": "Brawlstars",
    "created_utc": "2025-11-21T07:27:01.000Z",
    "url": "https://www.reddit.com/r/Brawlstars/comments/1p2sd3j/as_much_as_i_wanna_find_an_excuse_there_isnt/",
    "flair": "Discussion",
    "over_18": false,
    "is_self": false,
    "spoiler": false,
    "locked": false,
    "is_video": false,
    "domain": "i.redd.it",
    "thumbnail": "https://b.thumbs.redditmedia.com/4TPMNQFOrjTrD4MfDxxVEyJ_Jhju2thPN3vriMp1uhw.jpg",
    "url_overridden_by_dest": "https://i.redd.it/1jdqqymebk2g1.jpeg",
    "media": null,
    "media_metadata": null,
    "gallery_data": null
  }
]