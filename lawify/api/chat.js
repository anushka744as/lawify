const MODEL = "gemini-3-flash-preview";

const SYSTEM_PROMPT =
  "You are Lawify, an AI legal information assistant focused on Indian law. " +
  "Explain legal topics in plain, simple language. Always reply in the same language the user writes in. " +
  "Ask for details such as state, age or circumstances when they matter. " +
  "You provide general information, not legal advice; for serious matters suggest consulting a qualified lawyer.";

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(500).json({ error: "Server is missing GEMINI_API_KEY" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const messages = Array.isArray(body.messages) ? body.messages.slice(-20) : [];
  const contents = messages
    .filter((m) => m && typeof m.text === "string" && m.text.trim())
    .map((m) => ({
      role: m.role === "model" ? "model" : "user",
      parts: [{ text: m.text.slice(0, 4000) }],
    }));
  if (!contents.length) return res.status(400).json({ error: "No message provided" });

  try {
    const request = () =>
      fetch(`https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
          contents,
        }),
      });
    let r = await request();
    for (let i = 0; i < 2 && (r.status === 503 || r.status === 429); i++) {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      r = await request();
    }
    const data = await r.json();
    if (!r.ok) {
      return res.status(502).json({ error: (data.error && data.error.message) || "Gemini request failed" });
    }
    const parts = data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts;
    const reply = parts ? parts.map((p) => p.text || "").join("") : "";
    return res.status(200).json({ reply: reply || "Sorry, I couldn't generate an answer." });
  } catch (e) {
    return res.status(502).json({ error: "Could not reach Gemini" });
  }
};
