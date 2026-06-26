// WildAtlas - LLM extraction worker (Node ESM, short-lived)
//
// Reads a prompt from STDIN, calls the z-ai SDK, and prints the extracted
// JSON to stdout. Spawned as a short-lived child process by the enrichment
// watcher (the z-ai SDK crashes long-running processes after the first call,
// but works reliably in fresh short-lived processes).

import ZAI from "z-ai-web-dev-sdk";

async function main() {
  let prompt = "";
  for await (const chunk of process.stdin) prompt += chunk;
  if (!prompt) { console.log("{}"); return; }

  const killer = setTimeout(() => process.exit(1), 30_000);

  try {
    const zai = await ZAI.create();
    const response = await zai.chat.completions.create({
      messages: [{ role: "user", content: prompt }],
      thinking: { type: "disabled" },
    });
    const content = response.choices?.[0]?.message?.content ?? "";
    const cleaned = content
      .replace(/^```(?:json)?\s*/i, "")
      .replace(/\s*```$/i, "")
      .trim();
    console.log(cleaned);
  } catch {
    console.log("{}");
  } finally {
    clearTimeout(killer);
  }
}

main();
