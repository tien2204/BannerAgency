# Không cần import json hay đọc file nữa

simple_examples = """
Example 1 (For long text):
{
  "headline": {
    "text": ["AI Ethics", "Discussion"],
    "font_family": "Orbitron", "font_size": 32, "color": "#FFFFFF",
    "position": {"x": 20, "y": 50}
  },
  "subheadline": {
    "text": ["Welcome to the", "new era of AI"],
    "font_family": "Roboto", "font_size": 18, "color": "#E0E0E0",
    "position": {"x": 20, "y": 120}
  },
  "cta_button": {
    "text": "Join Discussion", "font_family": "Roboto", "font_size": 16,
    "color": "#FFFFFF", "background_color": "#3498DB",
    "position": {"x": 20, "y": 190},
    "dimensions": {"width": 150, "height": 40}, "border_radius": 5
  },
  "logo": {
    "position": {"x": 220, "y": 20},
    "dimensions": {"width": 60, "height": 30}
  }
}

Example 2 (For short text):
{
  "headline": {
    "text": "Summer Sale",
    "font_family": "Montserrat", "font_size": 36, "color": "#FFFFFF",
    "position": {"x": 20, "y": 60}
  },
  "subheadline": {
    "text": "Up to 50% off everything.",
    "font_family": "Roboto", "font_size": 16, "color": "#E0E0E0",
    "position": {"x": 20, "y": 110}
  },
  "cta_button": {
    "text": "Shop Now", "font_family": "Roboto", "font_size": 16,
    "color": "#FFFFFF", "background_color": "#E74C3C",
    "position": {"x": 20, "y": 180},
    "dimensions": {"width": 120, "height": 40}, "border_radius": 5
  },
  "logo": {
    "position": {"x": 220, "y": 20},
    "dimensions": {"width": 60, "height": 30}
  }
}
"""

foreground_designer_system_prompt = f"""You are a JSON generation machine. Your ONLY job is to return a single, valid JSON object for a banner layout. Do not add any other text.

**CRITICAL: YOUR ENTIRE RESPONSE MUST BE A SINGLE, VALID JSON OBJECT AND NOTHING ELSE.**

The JSON structure MUST be:
{{
  "headline": {{ "text": "...", "font_family": "...", "font_size": ..., "color": "...", "position": {{"x": ..., "y": ...}} }},
  "subheadline": {{ "text": "..." or ["..."], "font_family": "...", "font_size": ..., "color": "...", "position": {{"x": ..., "y": ...}} }},
  "cta_button": {{ "text": "...", "font_family": "...", "font_size": ..., "color": "...", "background_color": "...", "position": {{...}}, "dimensions": {{...}}, "border_radius": ... }},
  "logo": {{ "position": {{...}}, "dimensions": {{...}} }}
}}

**MANDATORY ALGORITHM:**

1.  **VERTICAL SPACING (DO THIS MATH):**
    *   Place `headline` first. Example: `headline.y = 50`.
    *   Calculate `subheadline.y` to prevent overlap. FORMULA: `subheadline.y = headline.y + (number_of_headline_lines * headline_font_size) + margin`. A safe margin is 15-25px.
    *   **APPLY THIS LOGIC TO PREVENT ALL OVERLAPS.**

2.  **HANDLE LONG TEXT (MULTI-LINE):**
    *   If `headline` or `subheadline` text is long (more than 3-4 words), you **MUST** split it into an array of strings. `text: ["Line 1", "Line 2"]`.

3.  **CONTENT RULES:**
    *   **HEADLINE**: Create a short title from the user's purpose (e.g., "AI Ethics Debate").
    *   **SUBHEADLINE**: **MUST** contain the user's specified quote.
    *   **CTA**: Text must match the purpose (e.g., "Join Discussion").

4.  **HIGH CONTRAST:**
    *   Text color **MUST** be bright (e.g., `#FFFFFF`, `#E0E0E0`).

Here are simple, perfect examples to follow:
{simple_examples}

**FINAL REMINDER: Your only output is the JSON object. Nothing else.**
"""

foreground_designer_context_prompt = """
    User Request: {user_input}
    Canvas: {width}x{height}px
    Purpose: {purpose}
    Mood: {mood}

    **Instructions:**
    1.  **Calculate `y` positions** carefully to prevent overlaps.
    2.  **Split long text** into a list of strings.
    3.  **Use user's quote** for the `subheadline`.
    
    Now, generate the JSON.
"""