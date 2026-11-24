# Bottom-of-funnel voiceover ads

Built from three reference ads and the user's copy breakdown. It hasn't been tested through review yet, so corrections from the user override anything here.

These ads sell the deal to people who already know the product. They're quick to make and meant to return strongly. The voiceover does the transaction and the visuals show the product.

**Every concept is three versions.** They share one body word for word. Only the voiceover hook, the hook text and the hook's B-roll change. Use a different hook type for each version where possible.

## Script

**Structure, in this order:**

| Stage | Job | Example |
|---|---|---|
| 1. Hook | Announce the deal and its urgency, or call out people who've been considering it | "It's the last day to get a pink LuxeLight at 50% off." |
| 2. Insider bridge (optional) | Make the next part feel like a tip, not an ad | "I'm going to tell you a little secret." |
| 3. Steps and no effort | Say what to tap and that the discount applies by itself | "If you click that link below and go all the way to checkout, they will automatically apply your coupons and discounts." |
| 4. Urgency close (optional) | Repeat the deadline before the video loops | "Just don't forget, the sale ends tonight." |

**Every script must have:**
- A specific deal.
- Physical steps, such as "click that link below" or "go all the way to checkout".
- Reassurance that the discount is easy to claim.
- No product explanation: no specs, ingredients, features or origin story.

**Hook types:**
- Deadline: "It's the last day to get…"
- How-to: "Here's how to get… on a triple discount."
- Fence-sitter: "If you've been thinking about grabbing this, do it now, because…" Only use this for products that have been on sale for a while. Nobody has been considering a product, or left it in their cart, if it has only just launched.
- New drop: "The new… just dropped, and…" For a new launch, lead with the fact that it's new.

**Don't recycle:** each new batch needs new hook angles, deal framing and text. Don't lean on lines from earlier ads, such as "3 FOR UNDER $67" or "ENDS TONIGHT". Different bundle prices and a current theme are good ways to get a fresh angle.

**The body's first line opens a loop:** it has to pull the same trigger as "I'm going to tell you a little secret", making the viewer feel they're about to get inside information and stay to hear it. It doesn't have to mention a secret. A flat line like "most people don't know this part" doesn't do this, and the user rejected it.

**Laying out scripts for review:** follow the order of the ad, with hooks 1, 2 and 3 first, then the body.

**Length:** aim for 40–50 words, about 10–13 seconds at around 4 words per second. Stay under 60 words. The references counted by hand are 35, 47 and 48 words, at 8.7–12.9 seconds.

**Keep the deal instantly clear:** the viewer shouldn't have to work anything out. State a simple price, such as "under $23 each", rather than a comparison like "three for less than the price of two".

**Voice:** casual and spoken, like someone tipping off a friend. Say "you" and "your", and "they" for the brand rather than "we". Link clauses with spoken connectors: "because", "if you", "and", "just don't forget". Avoid sales jargon.

**Offer claims:** take them from the brand's `CLAUDE.md`, and never invent a discount.

**Keep new scripts fresh:** copying the structure is the goal, and copying the lines isn't. Change at least the hook angle, plus one of the deal framing, the "secret" or the closing shot. The "secret" is the weakest beat in the references, so it's the best place for new ideas. Reusing one body across several hooks is deliberate, and those versions count as one concept.

## Edit

**Hook**
- Hook text is on screen from the first frame until the frame of the first cut. The whole hook is usually one continuous shot.
- Open on a visual event if possible. A light blasting on in the first second beats hands simply holding the product.
- The headtorch has to stay visible. Don't use a shot where the hook text covers the head or the product, even if no face is showing.
- Check AI clips (`hf_…`) for the product being generated wrongly, especially when it turns to show its back. If in doubt, use real footage in the hook.

**Hook text**
- Two lines: a coloured box with the deal, then a white box with black text and the urgency, such as "ENDS TONIGHT".
- The top line is the offer, ideally a money value such as "3 FOR UNDER $67" or "50% OFF". "LIMITED EDITION SALE" also works. Never lead with a question or a call-out like "STILL IN YOUR CART?", even when the spoken hook is a fence-sitter.
- The bottom line is urgency or scarcity, such as "ENDS TONIGHT" or "WHILE THE 8,000 LAST". "JUST DROPPED" doesn't count, because being new creates no pressure on its own.
- For variety, add an urgency emoji (🚨, ⚠️ or ‼️) to the bottom line on some versions, not all of them. Seasonal emoji need to read as the theme at a glance: the user rejected a sweet for Halloween and suggested 👻.
- The top line has to sound like a strong offer. The user rejected "2 FOR $51.99" as not sounding like much of a deal, along with the spoken hook built on it. Lead with a percentage off or a low "from" price rather than a bundle total.
- When the hook text is only a few words, make it bigger so it stands out. Set `hook_font_size` on that version.
- Match the user's CapCut text: the System font with Bold on, in capitals, in red and white boxes with slightly rounded corners, sitting in the upper part of the 4:5 box. `render.py` does this by default.
- It sums up the voiceover and doesn't repeat it word for word. Try to include the number, so people watching on mute see the deal.
- **Never repeat the urgency line across versions.** Changing only the top line while each version says "ENDS TONIGHT" reads as one hook. Give each version its own kind of pressure: time ("LAST DAY", "ENDS MIDNIGHT"), stock ("ONLY 8,000 MADE"), a season or new drop ("HALLOWEEN DROP"), or a stacked offer ("BOGO + FREE GIFT"). These are starting points to take inspiration from, so don't copy them word for word.

**Cuts**
- Cut on the first word of a sentence, within a frame or two.
- Each sentence gets one shot, so the references run about 5 shots in 12 seconds, at 1.6–3.6 seconds each.
- Time product actions to the words, such as the light switching on at "the sale ends tonight".

**Captions**
- White text with a dark outline, mostly lowercase with no end punctuation, centred, two lines at most.
- Split by spoken phrase, about 3–6 words each. Keep the deal in capitals, such as "50% OFF".
- Captions run during the hook as well, underneath the hook text. Set `captions_in_hook` in `config.json`.
- Check the caption doesn't run into a logo in the shot, or sit on top of the thing the line is showing.

**Footage**
- Keep the product on screen in nearly every shot, using a mix of first-person hands, stock in a warehouse, an overhead flat-lay, one person wearing it and the product working.
- Warehouse shots make the sale feel real, and fit the "secret" line.
- A finger pointing down suits "click that link below", and a person pointing to the product adds warmth.
- Show the product in the one colour the ad names. Check the background for other colours.
- Search the brand's whole footage library for each shot, not just the folder for that product or colour. Check accessories and packaging against what the user has shown as current.
