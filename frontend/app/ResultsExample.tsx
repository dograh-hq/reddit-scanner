// Static example placeholder shown in the results area BEFORE any workflow runs.
// Mirrors the real layout (post-card, filter tabs, jump badge, sections) with explainer
// text baked in so users understand the structure before they trigger their first run.
// Replaced by real <results> blocks as soon as the workflow produces data.
"use client";

export function ResultsExample() {
  return (
    <div className="results-example-wrap">
      <div className="results-example-header">
        <span className="results-example-badge">EXAMPLE — what your results will look like</span>
        <span className="results-example-hint">Run a workflow above to replace this with real data</span>
      </div>

      <div className="results-row">
        {/* ===== SECTION 1 EXAMPLE: Selected Posts with Suggested Comments =====
             Shows BOTH the high-score variant (top, white bg) and the low-score variant
             (slate-tinted, body collapsed) so the user understands the partition. */}
        <div className="results-section">
          <h2>Selected Posts with Suggested Comments</h2>

          <div className="filter-tabs-row">
            <div className="filter-tabs">
              <button className="filter-tab active" disabled>ALL</button>
              <button className="filter-tab" disabled>PASS</button>
              <button className="filter-tab" disabled>UNSURE</button>
              <button className="filter-tab" disabled>FAIL</button>
            </div>
            <span className="low-score-counts">
              <span className="low-score-counts-high">5 Posts ≥5 upvotes</span>
              <button className="low-score-counts-jump" disabled>3 Posts with &lt;5 ↓</button>
            </span>
          </div>
          <div className="example-callout">↑ Filter by validation tag · right-side count badge jumps you to low-upvote posts</div>

          {/* HIGH-score example card (white bg, full body) */}
          <div className="post-card example-card">
            <div className="example-tier-badge">HIGH-SIGNAL (≥5 upvotes) — these render at the top of the section</div>
            <div className="post-header">
              <div>
                <div className="post-title">
                  <a>Best practices for OSS voice agents <span className="example-inline">(post title — clickable Reddit link)</span></a>
                </div>
                <div className="post-sources">
                  <span className="post-source-chip"><a>[Link 1]</a><span className="post-source-name"> r/SaaS</span><span className="post-source-subs"> 250k</span></span>
                  <span className="post-source-chip"><a>[Link 2]</a><span className="post-source-name"> r/startups</span><span className="post-source-subs"> 1.5M</span></span>
                </div>
                <div className="example-callout">↑ Every subreddit the post appeared in (crossposts get a chip each)</div>
                <div className="post-meta">
                  <span>142 upvotes</span>
                  <span>23 comments</span>
                  <span>Discussion</span>
                </div>
              </div>
              <span className="tag-group">
                <span className="tag pass">pass</span>
                <span className="promo-chip">Promotional/Launch</span>
              </span>
            </div>
            <div className="example-callout">↑ Validation tag (PASS / UNSURE / FAIL) + Promotional/Launch chip if the LLM flagged it</div>

            <div className="post-summary">&quot;One-line LLM summary of the post — what it&apos;s actually about.&quot;</div>

            <div className="reasoning-box">
              <strong>Why selected:</strong> LLM reasoning for picking this post — alignment with your interests, engagement potential, etc.
            </div>

            <button className="collapsible-toggle" disabled>▸ Show 2 comment suggestions</button>
            <div className="example-callout">↑ Comments collapsed by default — click ▸ to reveal LLM-written suggestions + their validation scores</div>
          </div>

          {/* The italic partition banner that separates the two tiers in real results */}
          <div className="low-score-banner">
            ↓ Below posts have lower upvotes (less than 5)
          </div>

          {/* LOW-score example card (slate bg, comments still collapsed) */}
          <div className="post-card example-card low-score">
            <div className="example-tier-badge low">LOW-SIGNAL (&lt;5 upvotes) — slate-tinted, sits below the banner</div>
            <div className="post-header">
              <div>
                <div className="post-title"><a>Quick question on voice agent architecture</a></div>
                <div className="post-sources">
                  <span className="post-source-chip"><a>[Link]</a><span className="post-source-name"> r/AI_Agents</span><span className="post-source-subs"> 80k</span></span>
                </div>
                <div className="post-meta">
                  <span>2 upvotes</span>
                  <span>0 comments</span>
                </div>
              </div>
              <span className="tag-group">
                <span className="tag unsure">unsure</span>
              </span>
            </div>
            <div className="post-summary">&quot;Header data (title, sources, meta, tag, summary, why) stays visible.&quot;</div>
            <div className="reasoning-box">
              <strong>Why selected:</strong> Even low-upvote posts can be worth commenting on if relevance is high.
            </div>
            <button className="collapsible-toggle" disabled>▸ Show 2 comment suggestions</button>
            <div className="example-callout">↑ Same as high-signal cards but visually demoted — slate background signals lower priority</div>
          </div>
        </div>

        {/* ===== SECTION 2 EXAMPLE: Post Suggestions for Reddit and LinkedIn =====
             Same high/low partition as Section 1, but for low-score the STRATEGY block
             collapses (not just visual) since strategy is the heavy content here. */}
        <div className="results-section">
          <h2>Post Suggestions: For Reddit and LinkedIn</h2>

          <div className="filter-tabs-row">
            <div className="filter-tabs">
              <button className="filter-tab active" disabled>ALL</button>
              <button className="filter-tab" disabled>PASS</button>
              <button className="filter-tab" disabled>UNSURE</button>
              <button className="filter-tab" disabled>FAIL</button>
            </div>
            <span className="low-score-counts">
              <span className="low-score-counts-high">3 Posts ≥5 upvotes</span>
              <button className="low-score-counts-jump" disabled>2 Posts with &lt;5 ↓</button>
            </span>
          </div>

          {/* HIGH-score example card (full strategy visible) */}
          <div className="post-card example-card">
            <div className="example-tier-badge">HIGH-SIGNAL — strategy block always visible</div>
            <div className="post-header">
              <div>
                <div className="post-title"><a>Same post — also scored for repurposing as YOUR content</a></div>
                <div className="post-sources">
                  <span className="post-source-chip"><a>[Link]</a><span className="post-source-name"> r/SaaS</span><span className="post-source-subs"> 250k</span></span>
                </div>
                <div className="post-meta"><span>142 upvotes</span></div>
              </div>
              <span className="tag-group">
                <span className="tag pass">pass</span>
                <span className="promo-chip">Promotional/Launch</span>
              </span>
            </div>

            <div className="post-summary">&quot;Same one-line summary.&quot;</div>

            <div className="reasoning-box">
              <strong>Why it scores well:</strong> LLM reasoning — virality + fit, mentions whether it leans Reddit, LinkedIn, or both.
            </div>

            <div className="strategy-box">
              <div className="scores">
                <span className="score-item">Virality: <strong>8/10</strong></span>
                <span className="score-item">Fit: <strong>7/10</strong></span>
              </div>
              <div className="example-callout">↑ Virality + Fit (1–10). SELECT requires both ≥6.</div>
              <ul className="strategy-bullets">
                <li>Frame the post around your own experience</li>
                <li>Lead with the insight, not the company</li>
                <li>Best channel: LinkedIn</li>
              </ul>
              <div className="example-callout">↑ Bullet strategy — channel + framing tips for repurposing</div>
            </div>
          </div>

          {/* The italic partition banner */}
          <div className="low-score-banner">
            ↓ Below posts have lower upvotes (less than 5)
          </div>

          {/* LOW-score example card (strategy collapsed behind toggle) */}
          <div className="post-card example-card low-score">
            <div className="example-tier-badge low">LOW-SIGNAL — strategy block collapsed behind a toggle</div>
            <div className="post-header">
              <div>
                <div className="post-title"><a>Lower-upvote post still scored for repurposing fit</a></div>
                <div className="post-sources">
                  <span className="post-source-chip"><a>[Link]</a><span className="post-source-name"> r/buildinpublic</span><span className="post-source-subs"> 30k</span></span>
                </div>
                <div className="post-meta"><span>3 upvotes</span></div>
              </div>
              <span className="tag-group">
                <span className="tag unsure">unsure</span>
              </span>
            </div>
            <div className="post-summary">&quot;Header + summary + why-it-scores-well stays visible.&quot;</div>
            <div className="reasoning-box">
              <strong>Why it scores well:</strong> Reasoning still surfaces so you can decide whether to expand.
            </div>
            <button className="collapsible-toggle" disabled>▸ Show strategy &amp; validation</button>
            <div className="example-callout">↑ Strategy bullets + scores hidden — click to expand if the &quot;why&quot; looks promising</div>
          </div>
        </div>
      </div>

      {/* ===== SECTION 3 EXAMPLE: Rejected Posts (one-liner, no full card) ===== */}
      <div className="results-section">
        <h2>Rejected Posts</h2>
        <div className="example-callout-block">
          Posts the LLM said NO to during evaluation (Step 4). Title + meta + summary only — quick-scan to see what got filtered before commenting. The Promotional/Launch chip still appears here if relevant. Rejected posts are NOT partitioned by upvote count.
        </div>
      </div>
    </div>
  );
}
